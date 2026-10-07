"""Reproducible synthetic evaluation; does not claim physical validation."""
import json
import platform
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
from secondcut.fixtures import fixture
from secondcut.vision import inspect
from secondcut.planner import solve

results=[]
expected={'intact':'review','corner':'review','short':'review','notch':'review','reject':'replace','missing-marker':'recapture','perspective':'review','blur':'recapture','noise':'review'}
for kind,status in expected.items():
    started=time.perf_counter()
    result=inspect(fixture(kind))
    options=solve(result['mask']) if 'mask' in result else []
    actual=('review' if options else 'replace') if result['status']=='measured' else result['status']
    results.append({'sample':kind,'expected':status,'actual':actual,'passed':actual==status,'elapsed_ms':round((time.perf_counter()-started)*1000,2),'best_option':options[0] if options else None})
report={'dataset':'9 deterministic, generated images; NOT real photographs','opencv':cv2.__version__,'python':platform.python_version(),'platform':platform.platform(),'passed':sum(r['passed'] for r in results),'total':len(results),'physical_validation':'pending','results':results}
path=Path(__file__).resolve().parents[1]/'artifacts'/'evaluation.json'
path.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
