import hmac
import io
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .fixtures import fixture, mat
from .planner import solve, template_svg
from .vision import data_uri, inspect, SCALE
from .storage import ProjectStore

ROOT=Path(__file__).resolve().parent.parent
store=ProjectStore()
basic=HTTPBasic(auto_error=False)


def auth(credentials: Optional[HTTPBasicCredentials]=Depends(basic)):
    password=os.environ.get('SECONDCUT_PASSWORD')
    if password and (credentials is None or not hmac.compare_digest(credentials.username,'judge') or not hmac.compare_digest(credentials.password,password)):
        raise HTTPException(401,'Judge credentials required.',headers={'WWW-Authenticate':'Basic'})


app=FastAPI(title='SecondCut',version='0.1.0',dependencies=[Depends(auth)])
# Static assets contain no project data.
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')


class Settings(BaseModel):
    length:int=Field(180,ge=110,le=180)
    height:int=Field(70,ge=40,le=90)
    depth:int=Field(120,ge=60,le=180)
    min_length:int=Field(110,ge=60,le=180)
    min_height:int=Field(40,ge=25,le=90)
    thickness:float=Field(3,ge=1,le=6)


class Approval(BaseModel):
    option:int=Field(ge=0,le=2)


def save(project):
    store.save(project)


def get(project_id):
    project=store.get(project_id)
    if project is None:
        raise HTTPException(404,'Inspection not found.')
    return project


def uploaded_image(file):
    limit_mb=4 if os.environ.get('SECONDCUT_DEPLOYMENT')=='aws-lambda' else 10
    raw=file.file.read(limit_mb*1024*1024+1)
    if len(raw)>limit_mb*1024*1024:
        raise HTTPException(413,f'Image limit is {limit_mb} MB for this deployment.')
    # Check dimensions before decompressing, including highly compressed images.
    from PIL import Image
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in ('PNG','JPEG') or im.width*im.height>24_000_000:
                raise ValueError('Use a PNG/JPEG below 24 megapixels.')
        image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError('Unreadable photograph.')
        return image
    except Exception as e:
        raise HTTPException(400,'Use a readable PNG/JPEG below 24 megapixels.') from e


@app.get('/')
def home():
    return FileResponse(ROOT/'static'/'index.html')


@app.get('/api/health')
def health():
    return {'status':'ok','opencv':cv2.__version__,'opencv5':cv2.__version__.startswith('5.'),'deployment':os.environ.get('SECONDCUT_DEPLOYMENT','local'),'physical_validation':'pending'}


@app.get('/api/samples/{kind}')
def sample(kind:str):
    try:
        image=fixture(kind)
    except ValueError as e:
        raise HTTPException(404,str(e)) from e
    return Response(cv2.imencode('.png',image)[1].tobytes(),media_type='image/png')


@app.get('/api/mat.png')
def calibration_mat():
    from PIL import Image
    buf=io.BytesIO()
    Image.fromarray(cv2.cvtColor(mat(),cv2.COLOR_BGR2RGB)).save(buf,format='PNG',dpi=(76.2,76.2))
    return Response(buf.getvalue(),media_type='image/png',headers={'Content-Disposition':'attachment; filename="secondcut-a4-mat.png"'})


@app.post('/api/inspect')
def create_inspection(file:Optional[UploadFile]=File(None), demo:Optional[str]=Form(None), settings:str=Form('{}')):
    start=time.perf_counter()
    try:
        cfg=Settings.model_validate_json(settings)
        if cfg.min_length>cfg.length or cfg.min_height>cfg.height:
            raise ValueError('Minimum dimensions cannot exceed the original dimensions.')
    except Exception as e:
        raise HTTPException(422,str(e)) from e
    if (file is None)==(demo is None):
        raise HTTPException(400,'Choose one photograph or one synthetic sample.')
    if demo is not None:
        try:
            image=fixture(demo)
        except ValueError as e:
            raise HTTPException(400,str(e)) from e
    else:
        image=uploaded_image(file)
    result=inspect(image)
    project={'id':str(uuid.uuid4()),'created_at':time.time(),'settings':cfg.model_dump(),'source':'synthetic fixture' if demo else 'user photograph','sample':demo,'opencv':cv2.__version__,'approved':None,'verification':None}
    project.update({k:v for k,v in result.items() if k not in ('mask','rectified')})
    if result['status']=='measured':
        options=solve(result['mask'],cfg.length,cfg.height,cfg.min_length,cfg.min_height)
        project['options']=options
        project['status']='review' if options else 'replace'
        project['message']='Review the repair dimensions before exporting a cutting template.' if options else 'No rectangular blank meets your minimum dimensions with a 2 mm edge allowance. Replace this panel or revise your requirements.'
        original_area=cfg.length*cfg.height
        for opt in options:
            opt['retained_area_mm2']=opt['length']*opt['height']
            opt['retained_percent']=round(opt['retained_area_mm2']/original_area*100,1)
            opt['companion']={'length':cfg.depth,'height':opt['height'],'slot_width':cfg.thickness,'slot_depth':opt['height']/2}
            overlay=result['rectified'].copy()
            x,y,w,h=(opt[k] for k in ('x','y','length','height'))
            cv2.rectangle(overlay,(x*SCALE,y*SCALE),((x+w)*SCALE,(y+h)*SCALE),(87,168,25),3)
            opt['overlay']=data_uri(overlay)
        project['image']=data_uri(result['rectified'])
        project['trace'] += [{'tool':'search_recovery_rectangles','result':f'{len(options)} alternatives satisfy minimum dimensions and a 2 mm edge allowance.'}, {'tool':'propagate_joint_constraints','result':'Both panels share the new height; both slots are half that height and use the entered thickness.'}, {'tool':'request_human_review' if options else 'request_replacement','result':project['message']}]
    project['elapsed_ms']=round((time.perf_counter()-start)*1000,1)
    save(project)
    return project


@app.post('/api/projects/{project_id}/approve')
def approve(project_id:str, approval:Approval):
    project=get(project_id)
    if project['status']!='review' or approval.option>=len(project.get('options',[])):
        raise HTTPException(409,'This inspection has no such repair option.')
    project['approved']=approval.option
    project['verification']=None
    project['trace'].append({'tool':'human_approval','result':f'User accepted option {approval.option+1}. Template export enabled.'})
    save(project)
    return project


@app.get('/api/projects/{project_id}/template.svg')
def template(project_id:str):
    project=get(project_id)
    if project['approved'] is None:
        raise HTTPException(409,'Review and accept a repair first.')
    opt=project['options'][project['approved']]
    cfg=project['settings']
    svg=template_svg(opt['length'],opt['height'],cfg['depth'],cfg['thickness'])
    return Response(svg,media_type='image/svg+xml',headers={'Content-Disposition':'attachment; filename="secondcut-repair.svg"'})


@app.post('/api/projects/{project_id}/verify')
def verify(project_id:str,file:Optional[UploadFile]=File(None),demo:bool=Form(False)):
    project=get(project_id)
    if project['approved'] is None:
        raise HTTPException(409,'Accept a repair before verifying it.')
    if (file is None)==(not demo):
        raise HTTPException(400,'Choose either a new photograph or the synthetic repaired sample.')
    opt=project['options'][project['approved']]
    w,h=opt['length'],opt['height']
    if demo:
        img=mat()
        cv2.rectangle(img,(15*SCALE,90*SCALE),((15+w)*SCALE-1,(90+h)*SCALE-1),(94,156,198),-1)
        t=project['settings']['thickness']
        cv2.rectangle(img,(round((15+w/2-t/2)*SCALE),90*SCALE),(round((15+w/2+t/2)*SCALE)-1,round((90+h/2)*SCALE)-1),(255,255,255),-1)
    else:
        img=uploaded_image(file)
    measured=inspect(img)
    if measured['status']!='measured':
        return {k:v for k,v in measured.items() if k not in ('mask','rectified')}
    mask=measured['mask']; ys,xs=np.where(mask)
    actual_w=int(xs.max()-xs.min()+1);actual_h=int(ys.max()-ys.min()+1)
    cropped=mask[ys.min():ys.max()+1,xs.min():xs.max()+1].astype(np.uint8)
    normalized=cv2.resize(cropped,(w*SCALE,h*SCALE),interpolation=cv2.INTER_NEAREST)>0
    expected=np.ones((h*SCALE,w*SCALE),bool)
    t=project['settings']['thickness']
    expected[:round(h*SCALE/2),round((w-t)*SCALE/2):round((w+t)*SCALE/2)]=False
    # IoU alone hides narrow missing slots; separately measure the expected slot.
    iou=float(np.logical_and(normalized,expected).sum()/np.logical_or(normalized,expected).sum())
    slot=~expected
    slot_clear=float((~normalized[slot]).mean())
    good=abs(actual_w-w)<=3 and abs(actual_h-h)<=3 and iou>=0.94 and slot_clear>=0.75
    verification={'status':'geometry_matches' if good else 'needs_correction','source':'synthetic fixture' if demo else 'user photograph','measured_mm':[actual_w,actual_h],'target_mm':[w,h],'silhouette_iou':round(iou,4),'slot_clear_fraction':round(slot_clear,4),'message':'Panel outline and slot match within prototype tolerances. Physical assembly fit still requires a hands-on check.' if good else 'The panel outline or slot differs from the accepted template. Check the highlighted target and measure again.','image':data_uri(measured['rectified'])}
    project['verification']=verification
    project['trace'].append({'tool':'verify_recaptured_geometry','result':f"{verification['status']}; source={verification['source']}; silhouette IoU={iou:.3f}; slot clearance={slot_clear:.3f}."})
    save(project)
    return verification


@app.get('/api/projects/{project_id}/report.json')
def report(project_id:str):
    project=get(project_id)
    project.pop('image',None)
    for opt in project.get('options',[]):
        opt.pop('overlay',None)
    if project.get('verification'):
        project['verification'].pop('image',None)
    return Response(json.dumps(project,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="secondcut-inspection.json"'})
