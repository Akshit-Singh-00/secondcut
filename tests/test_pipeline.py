import json
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from secondcut.app import app
from secondcut.fixtures import fixture, mat
from secondcut.vision import inspect, SCALE
from secondcut.planner import solve, template_svg

client=TestClient(app)

@pytest.mark.parametrize('kind',['intact','corner','short','notch','perspective','noise'])
def test_recovery_is_inside_actual_material(kind):
    result=inspect(fixture(kind))
    assert result['status']=='measured'
    options=solve(result['mask'])
    assert options
    for p in options:
        x,y,w,h=(p[k] for k in ('x','y','length','height'))
        assert result['mask'][y-2:y+h+2,x-2:x+w+2].all()
        assert 110<=w<=180 and 40<=h<=70


@pytest.mark.parametrize('kind',['missing-marker','blur'])
def test_uncertain_capture_cannot_produce_a_plan(kind):
    result=inspect(fixture(kind))
    assert result['status']=='recapture'
    assert 'mask' not in result


def test_unrecoverable_rejected():
    result=inspect(fixture('reject'))
    assert result['status']=='measured'
    assert solve(result['mask'])==[]


def test_alternatives_offer_real_dimension_tradeoffs():
    options=solve(inspect(fixture('corner'))['mask'])
    assert len(options)>=2
    assert max(p['length'] for p in options)>=170
    for a in options:
        for b in options:
            if a is not b:
                assert not (a['length']<=b['length'] and a['height']<=b['height'])


def test_internal_hole_never_filled():
    result=inspect(fixture('hole'))
    assert not result['mask'][125,105]
    for p in solve(result['mask'],min_length=60,min_height=25):
        assert result['mask'][p['y']:p['y']+p['height'],p['x']:p['x']+p['length']].all()


def test_solver_matches_brute_force_on_small_random_masks():
    rng=np.random.default_rng(32)
    for _ in range(20):
        mask=rng.random((10,14))>0.15
        options=solve(mask,length=8,height=6,min_length=2,min_height=2,margin=0)
        best=0
        for h in range(2,7):
            for w in range(2,9):
                for y in range(11-h):
                    for x in range(15-w):
                        if mask[y:y+h,x:x+w].all():
                            best=max(best,w*h)
        assert (options[0]['length']*options[0]['height'] if options else 0)==best


def test_approval_export_verification_loop():
    res=client.post('/api/inspect',data={'demo':'corner'})
    assert res.status_code==200
    p=res.json(); pid=p['id']
    assert p['source']=='synthetic fixture'
    assert client.get(f'/api/projects/{pid}/template.svg').status_code==409
    assert client.post(f'/api/projects/{pid}/approve',json={'option':2**10}).status_code==422
    accepted=client.post(f'/api/projects/{pid}/approve',json={'option':0}).json()
    assert accepted['approved']==0
    svg=client.get(f'/api/projects/{pid}/template.svg')
    assert svg.status_code==200 and 'separate stock required' in svg.text
    verified=client.post(f'/api/projects/{pid}/verify',data={'demo':'true'})
    assert verified.status_code==200
    assert verified.json()['status']=='geometry_matches',verified.json()
    report=client.get(f'/api/projects/{pid}/report.json').json()
    assert report['verification']['source']=='synthetic fixture'
    assert report['trace'][-1]['tool']=='verify_recaptured_geometry'


def test_unslotted_panel_fails_verification():
    p=client.post('/api/inspect',data={'demo':'corner'}).json()
    client.post(f"/api/projects/{p['id']}/approve",json={'option':0})
    option=p['options'][0]
    img=mat()
    cv2.rectangle(img,(45,270),((15+option['length'])*SCALE-1,(90+option['height'])*SCALE-1),(94,156,198),-1)
    raw=cv2.imencode('.png',img)[1].tobytes()
    result=client.post(f"/api/projects/{p['id']}/verify",files={'file':('panel.png',raw,'image/png')}).json()
    assert result['status']=='needs_correction'
    assert result['slot_clear_fraction']<0.75


def test_input_validation_and_bad_image():
    assert client.post('/api/inspect').status_code==400
    assert client.post('/api/inspect',data={'demo':'unknown'}).status_code==400
    assert client.post('/api/inspect',data={'demo':'corner','settings':json.dumps({'thickness':-1})}).status_code==422
    assert client.post('/api/inspect',data={'demo':'corner','settings':json.dumps({'min_height':80,'height':70})}).status_code==422
    assert client.post('/api/inspect',files={'file':('bad.png',b'not a picture','image/png')}).status_code==400


def test_no_markers_and_multiple_blanks_rejected():
    assert inspect(np.full((900,650,3),255,np.uint8))['status']=='recapture'
    image=fixture('intact')
    cv2.rectangle(image,(150,600),(330,700),(94,156,198),-1)
    assert inspect(image)['status']=='recapture'


def test_production_password_gate(monkeypatch):
    monkeypatch.setenv('SECONDCUT_PASSWORD','test-only-password')
    assert client.get('/api/health').status_code==401
    assert client.get('/api/health',auth=('judge','test-only-password')).status_code==200


def test_version_requirement():
    assert cv2.__version__.startswith('5.')
