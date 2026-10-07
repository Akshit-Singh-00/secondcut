"""A bounded solver. A repair is valid only when the whole blank fits."""
import cv2
import numpy as np


def solve(mask, length=180, height=70, min_length=110, min_height=40, margin=2):
    safe = cv2.erode(np.uint8(mask), np.ones((margin*2+1,margin*2+1),np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0)
    histogram = np.zeros(safe.shape[1],dtype=int)
    candidates = {}
    # Largest-rectangle histogram with bounded target dimensions, O(pixels).
    for y,row in enumerate(safe):
        histogram = np.where(row, histogram+1, 0)
        stack = []
        for x,h in enumerate(np.append(histogram,0)):
            start = x
            while stack and stack[-1][1] > h:
                left,hh = stack.pop()
                w,hh = min(x-left,length), min(int(hh),height)
                if w >= min_length and hh >= min_height:
                    item = {'x':int(left),'y':int(y-hh+1),'length':int(w),'height':int(hh)}
                    candidates[(w,hh)] = item
                start = left
            if not stack or stack[-1][1] < h:
                stack.append((start,int(h)))
    if not candidates:
        return []
    # Discard dimensions that are worse in both axes than another option.
    frontier=[]
    tallest=0
    for r in sorted(candidates.values(),key=lambda r:(r['length'],r['height']),reverse=True):
        if r['height']>tallest:
            frontier.append(r)
            tallest=r['height']
    ranked = sorted(frontier, key=lambda r:(r['length']*r['height'],r['length'],r['height']), reverse=True)
    # Show a few meaningful trade-offs, not nearly identical placements.
    chosen=[]
    for r in ranked:
        if all(abs(r['length']-c['length'])+abs(r['height']-c['height']) >= 8 for c in chosen):
            chosen.append(r)
        if len(chosen)==3:
            break
    return chosen


def template_svg(length,height,depth,thickness):
    # Two half-lap panels. This is an insert, without a base or exterior walls.
    t=thickness
    def path(x,y,w,h,top):
        mid=w/2
        if top:
            pts=[(0,0),(mid-t/2,0),(mid-t/2,h/2),(mid+t/2,h/2),(mid+t/2,0),(w,0),(w,h),(0,h)]
        else:
            pts=[(0,0),(w,0),(w,h),(mid+t/2,h),(mid+t/2,h/2),(mid-t/2,h/2),(mid-t/2,h),(0,h)]
        return 'M '+' L '.join(f'{x+a:.2f},{y+b:.2f}' for a,b in pts)+' Z'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">
<rect width="210" height="297" fill="white"/><g font-family="Arial" fill="#172b28"><text x="15" y="12" font-size="5">SecondCut · recovery template</text>
<text x="15" y="20" font-size="3">Print at 100%. Check scale. Solid lines are cuts. No machine control.</text>
<text x="15" y="27" font-size="3">A · salvaged blank · {length} × {height} mm</text>
<text x="15" y="{height+47}" font-size="3">B · companion blank · {depth} × {height} mm · separate stock required</text>
<text x="15" y="240" font-size="3">Slots: {thickness} mm. Test on spare material; physical fit is not certified.</text>
<text x="15" y="247" font-size="3">Both slots reach half the shared height; slide the panels together.</text>
<text x="15" y="254" font-size="3">Use inside an existing box/tray. This insert has no base or outer walls.</text>
<text x="15" y="282" font-size="3">Scale check: line below must measure exactly 50 mm.</text></g>
<g fill="none" stroke="#172b28" stroke-width="0.25"><path d="{path(15,32,length,height,True)}"/><path d="{path(15,height+52,depth,height,False)}"/>
<path d="M15 287H65 M15 285V289 M65 285V289"/></g></svg>'''
