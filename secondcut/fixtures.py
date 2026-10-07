"""Deterministic generated images, explicitly synthetic, never physical evidence."""
import cv2
import numpy as np
from .vision import SCALE,CENTERS,WIDTH,HEIGHT


def mat():
    image=np.full((HEIGHT*SCALE,WIDTH*SCALE,3),255,np.uint8)
    dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for i,(x,y) in enumerate(CENTERS):
        marker=cv2.aruco.generateImageMarker(dictionary,i,20*SCALE)
        x,y=int((x-10)*SCALE),int((y-10)*SCALE)
        image[y:y+20*SCALE,x:x+20*SCALE]=cv2.cvtColor(marker,cv2.COLOR_GRAY2BGR)
    return image


def fixture(kind='corner', seed=7):
    image=mat()
    x,y,w,h=15*SCALE,90*SCALE,180*SCALE,70*SCALE
    cv2.rectangle(image,(x,y),(x+w-1,y+h-1),(94,156,198),-1)
    if kind=='corner':
        cv2.rectangle(image,(x+w-32*SCALE,y),(x+w,y+23*SCALE),(255,255,255),-1)
    elif kind=='short':
        cv2.rectangle(image,(x+142*SCALE,y),(x+w,y+h),(255,255,255),-1)
    elif kind=='notch':
        cv2.rectangle(image,(x+76*SCALE,y),(x+96*SCALE,y+22*SCALE),(255,255,255),-1)
    elif kind=='reject':
        cv2.rectangle(image,(x+85*SCALE,y),(x+w,y+h),(255,255,255),-1)
    elif kind=='missing-marker':
        cv2.rectangle(image,(0,0),(30*SCALE,30*SCALE),(255,255,255),-1)
    elif kind=='hole':
        cv2.circle(image,(x+90*SCALE,y+35*SCALE),12*SCALE,(255,255,255),-1)
    elif kind=='blur':
        image=cv2.GaussianBlur(image,(31,31),10)
    elif kind not in ('intact','perspective','noise'):
        raise ValueError('Unknown sample.')
    if kind=='noise':
        rng=np.random.default_rng(seed)
        image=np.uint8(np.clip(image.astype(float)+rng.normal(0,5,image.shape),0,255))
    if kind=='perspective':
        src=np.float32([[0,0],[629,0],[629,890],[0,890]])
        dst=np.float32([[75,40],[670,5],[710,925],[15,870]])
        image=cv2.warpPerspective(image,cv2.getPerspectiveTransform(src,dst),(750,960),borderValue=(235,235,235))
    return image
