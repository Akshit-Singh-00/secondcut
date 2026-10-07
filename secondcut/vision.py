"""OpenCV 5 perception. One planar, contrasting blank on a known A4 mat."""
import base64
import cv2
import numpy as np

SCALE = 3
WIDTH, HEIGHT = 210, 297
CENTERS = np.array([[15, 15], [195, 15], [195, 282], [15, 282]], np.float32)


def data_uri(img):
    ok, data = cv2.imencode('.png', img)
    if not ok:
        raise ValueError('Could not encode inspection evidence.')
    return 'data:image/png;base64,' + base64.b64encode(data).decode()


def inspect(image):
    if image is None or image.size == 0:
        raise ValueError('Upload a readable PNG or JPEG photograph.')
    if max(image.shape[:2]) > 2600:
        image = cv2.resize(image, None, fx=2600/max(image.shape[:2]), fy=2600/max(image.shape[:2]))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50))
    corners, ids, _ = detector.detectMarkers(gray)
    found = {} if ids is None else {int(i): c[0].mean(axis=0) for c, i in zip(corners, ids.flatten())}
    missing = [i for i in range(4) if i not in found]
    trace = [{'tool': 'detect_calibration_markers', 'result': f'Found {4-len(missing)}/4 required markers.'}]
    if missing:
        return {'status': 'recapture', 'message': 'Show all four mat markers, flatten the mat, and move closer until the markers are sharp.', 'trace': trace, 'missing_markers': missing}
    src = np.array([found[i] for i in range(4)], np.float32)
    if not cv2.isContourConvex(src.reshape(-1, 1, 2)) or abs(cv2.contourArea(src)) < 20000:
        return {'status': 'recapture', 'message': 'Move closer and photograph the whole flat mat from above.', 'trace': trace}
    transform = cv2.getPerspectiveTransform(src, CENTERS * SCALE)
    rectified = cv2.warpPerspective(image, transform, (WIDTH*SCALE, HEIGHT*SCALE), borderValue=(255,255,255))
    hsv = cv2.cvtColor(rectified, cv2.COLOR_BGR2HSV)
    # Brown/coloured, matte cardboard against the white mat. No semantic material identification.
    mask = cv2.inRange(hsv, np.array([0, 38, 35]), np.array([179, 255, 245]))
    allowed = np.zeros_like(mask)
    allowed[32*SCALE:265*SCALE, 8*SCALE:202*SCALE] = 255
    mask = cv2.bitwise_and(mask, allowed)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    large = [i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA] > 150*SCALE*SCALE]
    if len(large) != 1:
        return {'status': 'recapture', 'message': 'Place one flat brown cardboard blank inside the mat, remove other objects, and use even lighting.', 'trace': trace + [{'tool':'segment_material', 'result':f'Found {len(large)} substantial regions; expected one.'}], 'image':data_uri(rectified)}
    mask = np.uint8(labels == large[0])*255
    # Reject cropped parts: never assume a hidden boundary is usable material.
    ys,xs = np.where(mask > 0)
    if xs.min() <= 8*SCALE+2 or xs.max() >= 202*SCALE-3 or ys.min() <= 32*SCALE+2 or ys.max() >= 265*SCALE-3:
        return {'status':'recapture', 'message':'Move the entire blank away from the capture-area border.', 'trace':trace, 'image':data_uri(rectified)}
    edge = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, np.ones((5,5),np.uint8)) > 0
    sharpness = float(np.mean(np.abs(cv2.Laplacian(cv2.cvtColor(rectified,cv2.COLOR_BGR2GRAY),cv2.CV_64F))[edge]))
    if sharpness < 9:
        return {'status':'recapture', 'message':'The material edge is too soft to measure. Hold the camera still and focus on the cardboard.', 'trace':trace + [{'tool':'check_edge_quality','result':f'Edge sharpness {sharpness:.1f} below threshold 9.'}], 'image':data_uri(rectified)}
    # Keep internal holes. Downsample conservatively: every source pixel must be material.
    mm_mask = cv2.resize(mask, (WIDTH,HEIGHT), interpolation=cv2.INTER_AREA) >= 254
    trace += [{'tool':'rectify_plane','result':'Four marker centers mapped to an A4 plane at 3 pixels/mm.'}, {'tool':'segment_material','result':f'{int(mm_mask.sum())} mm² visible material; holes preserved.'}, {'tool':'check_edge_quality','result':f'Edge sharpness {sharpness:.1f}; passed threshold 9.'}]
    return {'status':'measured', 'mask':mm_mask, 'rectified':rectified, 'trace':trace, 'area_mm2':int(mm_mask.sum()), 'edge_sharpness':round(sharpness,1)}
