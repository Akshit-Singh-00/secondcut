"""Test a running endpoint with synthetic inputs; credentials are never saved."""
import argparse
import base64
import getpass
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('artifacts/runtime/endpoint-check.json'))
    args = parser.parse_args()
    base = args.url.rstrip('/')
    parts = urlsplit(base)
    if parts.username or parts.password or parts.query or parts.fragment:
        parser.error('Use a base URL without credentials, query, or fragment.')
    if args.local:
        if parts.scheme != 'http' or parts.hostname not in ('127.0.0.1', 'localhost'):
            parser.error('--local is restricted to HTTP localhost.')
    elif parts.scheme != 'https':
        parser.error('Hosted judge credentials require HTTPS.')
    password = None if args.local else getpass.getpass('Judge password (not saved): ')
    opener = build_opener(NoRedirect())
    evidence = {'checked_at': datetime.now(timezone.utc).isoformat(), 'endpoint': base,
                'source': 'synthetic fixtures', 'checks': [],
                'limits': 'No physical validation or cold-start/S3 durability claim.'}

    def expect(path, expected=200, method='GET', form=None, payload=None, authenticated=True):
        headers, data = {}, None
        if form is not None:
            data = urlencode(form).encode()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if payload is not None:
            data = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        if password and authenticated:
            token = base64.b64encode(('judge:' + password).encode()).decode()
            headers['Authorization'] = 'Basic ' + token
        start = time.perf_counter()
        try:
            with opener.open(Request(base + path, data=data, headers=headers, method=method), timeout=60) as response:
                status, body = response.status, response.read()
        except HTTPError as error:
            status, body = error.code, error.read()
        evidence['checks'].append({'method': method, 'path': path, 'http_status': status,
                                   'elapsed_ms': round((time.perf_counter()-start)*1000, 1)})
        if status != expected:
            raise RuntimeError(f'{path}: expected HTTP {expected}, received {status}')
        return body

    try:
        if not args.local:
            expect('/api/health', 401, authenticated=False)
        health = json.loads(expect('/api/health'))
        if not health.get('opencv5'):
            raise RuntimeError('Endpoint is not reporting OpenCV 5.')
        if not args.local and health.get('deployment') != 'aws-lambda':
            raise RuntimeError('Hosted endpoint is not reporting aws-lambda.')
        evidence['health'] = health
        ids = {}
        for sample, decision in [('corner', 'review'), ('short', 'review'), ('notch', 'review'), ('reject', 'replace'), ('missing-marker', 'recapture')]:
            result = json.loads(expect('/api/inspect', method='POST', form={'demo': sample}))
            if result['status'] != decision or result['source'] != 'synthetic fixture':
                raise RuntimeError(f'{sample}: expected {decision} with synthetic provenance')
            ids[sample] = result['id']
        path = '/api/projects/' + ids['corner']
        expect(path + '/template.svg', 409)
        expect(path + '/approve', method='POST', payload={'option': 0})
        template = expect(path + '/template.svg')
        if b'<svg' not in template or b'separate stock' not in template:
            raise RuntimeError('Expected SVG and companion stock note were absent.')
        result = json.loads(expect(path + '/verify', method='POST', form={'demo': 'true'}))
        if result['status'] != 'geometry_matches':
            raise RuntimeError('Synthetic panel failed geometry verification.')
        report = json.loads(expect(path + '/report.json'))
        if report['approved'] != 0 or report['verification']['status'] != 'geometry_matches':
            raise RuntimeError('Stored report lost approval or verification.')
        evidence.update(status='passed', project_ids=ids)
    except Exception as error:
        evidence.update(status='failed', error=str(error))
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        print(f"{evidence['status']}: {args.output}")


if __name__ == '__main__':
    main()
