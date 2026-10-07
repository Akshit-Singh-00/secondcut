"""Build an explicit allowlisted judge package, excluding credentials/runtime data."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
files=[]
allowed_extensions = {
    'secondcut': {'.py'}, 'static': {'.html', '.css', '.js', '.svg'},
    'tests': {'.py'}, 'scripts': {'.py'}, 'docs': {'.md', '.html', '.json', '.svg'},
    'output/pdf': {'.pdf'},
}
for folder, extensions in allowed_extensions.items():
    files.extend(p for p in (root/folder).rglob('*')
                 if p.is_file() and p.suffix in extensions
                 and not any(part.startswith('.') or part=='__pycache__'
                             for part in p.relative_to(root/folder).parts))
# Never include deployment.json or other account-specific configuration.
files.extend(root/'infra'/name for name in ('README.md', 'template.yaml'))
for name in ('README.md','Dockerfile','requirements.txt','requirements-dev.txt','requirements.lock.txt','.dockerignore'):
    files.append(root/name)
for name in ('evaluation.json','calibration-mat.png','workbench.png','repair-review.png','verification.png','recapture.png','architecture.png','secondcut-software-walkthrough.mp4'):
    p=root/'artifacts'/name
    if p.exists():files.append(p)
destination=root/'artifacts'/'secondcut-review-package.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):
        z.write(p,p.relative_to(root))
print(f'{destination}\n{len(files)} files; {destination.stat().st_size:,} bytes')
