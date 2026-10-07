import html
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'docs'/'submission.json').read_text(encoding='utf-8'))
fields=[('Project name',data['project_name']),('Elevator pitch',data['elevator_pitch']),('Built with',', '.join(data['built_with'])),('Repository',data['repository_url']+'\n'+data['repository_status']),('Working endpoint',data['working_web_endpoint'] or 'Pending verified AWS deployment'),('Video URL',data['video_demo_url'] or 'Pending final hosted demo'),('Special awards','None selected; eligibility not claimed'),('Project story',data['about_project']),('Testing instructions',data['testing_instructions'])]
sections=''.join(f'<section><h2>{html.escape(label)}</h2><pre>{html.escape(value)}</pre></section>' for label,value in fields)
pending=''.join(f'<li>{html.escape(x)}</li>' for x in data['pending_before_final_review'])
doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SecondCut - submission review</title><style>body{{font:16px/1.7 system-ui;background:#f6f5ef;color:#203b32;max-width:920px;margin:40px auto;padding:0 24px}}h1{{font-size:40px;letter-spacing:-1px}}h2{{font-size:18px}}section{{background:#fffef9;border:1px solid #d7dfcf;padding:22px;margin:18px 0;border-radius:12px}}pre{{font:14px/1.8 system-ui;white-space:pre-wrap;overflow-wrap:anywhere}}.status{{padding:20px;background:#fae8df;border-radius:12px}}a{{color:#3e6751}}</style></head><body><h1>SecondCut / review the answers</h1><p>Prepared 7 October 2026. This page contains the exact current draft wording. Final submission has not been authorized.</p><div class="status"><strong>Not ready for final submission</strong><ul>{pending}</ul></div>{sections}<p><a href="https://devpost.com/submit-to/30984-opencv-ai-competition-2026-powered-by-aws/manage/submissions/1222437-secondcut/project-overview">Open the Devpost draft</a></p></body></html>'''
(root/'docs'/'submission-review.html').write_text(doc,encoding='utf-8')
print(root/'docs'/'submission-review.html')
