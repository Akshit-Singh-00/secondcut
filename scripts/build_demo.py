"""Create a silent annotated walkthrough from genuine app screenshots.

Install the optional authoring dependency: imageio-ffmpeg==0.6.0.
This is a draft montage, not a continuous screen recording or physical demo.
"""
from pathlib import Path
import textwrap
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'/'secondcut-software-walkthrough.mp4'
W,H=1280,720
font_path=Path('C:/Windows/Fonts/segoeui.ttf')
bold_path=Path('C:/Windows/Fonts/segoeuib.ttf')
def font(size,bold=False):
    path=bold_path if bold else font_path
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default(size=size)
scenes=[
    ('SecondCut','A wrong cut. A workable next step.',None,8,'SOFTWARE WALKTHROUGH DRAFT'),
    ('Measure what remains','Real OpenCV 5 pipeline. These demonstration inputs are synthetic.','workbench.png',14,'01 / CAPTURE + INSPECT'),
    ('Choose a compatible recovery','143 x 66 mm main panel; matching half-height slots in both panels.','repair-review.png',12,'02 / REVIEW + ACCEPT'),
    ('Check the next cut','The generated repaired panel passes visible geometry checks. Physical fit is unverified.','verification.png',12,'03 / RECAPTURE + VERIFY'),
    ('Ask for better evidence','Missing calibration markers trigger recapture, not an invented measurement.','recapture.png',10,'FAILURE HANDLING'),
    ('The system behind the decision','Local backend works. Lambda, private S3, and CloudWatch deployment are prepared only.','architecture.png',14,'ARCHITECTURE'),
    ('Evidence, with honest limits','18 automated tests pass. 9 of 9 generated scenarios match expected decisions.',None,10,'VALIDATION'),
    ('Before the final submission','AWS deployment, real cardboard validation, participant introduction, and final hosted video remain pending.',None,8,'REVIEW DRAFT - NOT A FINAL ENTRY')
]
writer=imageio_ffmpeg.write_frames(str(OUT),(W,H),fps=12,codec='libx264',pix_fmt_in='rgb24',pix_fmt_out='yuv420p',output_params=['-crf','23','-movflags','+faststart'])
writer.send(None)
for index,(title,caption,file,seconds,label) in enumerate(scenes):
    frame=Image.new('RGB',(W,H),'#f6f5ef');d=ImageDraw.Draw(frame)
    d.text((40,26),label,fill='#db643b',font=font(16,True))
    d.text((40,57),title,fill='#203b32',font=font(34,True))
    if file:
        im=Image.open(ROOT/'artifacts'/file).convert('RGB')
        # A screenshot montage. No alteration of content, only aspect-preserving placement.
        if file=='workbench.png':
            # Full page scrolls within the content area so the UI stays readable.
            scaled=im.resize((790,round(im.height*790/im.width)))
        else:
            im.thumbnail((1160,460),Image.Resampling.LANCZOS)
            scaled=im
    else:
        d.rounded_rectangle((40,140,1240,565),radius=24,fill='#e8eee0')
        if index==0:
            d.text((85,235),'secondcut.',fill='#203b32',font=font(95,True))
            d.text((90,365),'Akshit Singh | OpenCV AI Competition 2026',fill='#61765a',font=font(24))
            d.text((90,410),'Annotated screenshots of the running local prototype',fill='#61765a',font=font(20))
        else:
            lines=textwrap.wrap(caption,width=60)
            for n,line in enumerate(lines):d.text((80,245+n*45),line,fill='#203b32',font=font(29))
    for n,line in enumerate(textwrap.wrap(caption,width=95)):
        d.text((40,607+n*30),line,fill='#203b32',font=font(23))
    d.text((40,687),'Generated fixtures are not evidence of real-world accuracy or physical assembly.',fill='#748178',font=font(14))
    d.text((1170,687),f'{index+1} / {len(scenes)}',fill='#748178',font=font(14))
    for j in range(seconds*12):
        current=frame.copy()
        if file:
            if file=='workbench.png':
                offset=round(max(0,scaled.height-460)*j/max(1,seconds*12-1))
                crop=scaled.crop((0,offset,scaled.width,min(offset+460,scaled.height)))
                current.paste(crop,((W-crop.width)//2,125))
            else:
                current.paste(scaled,((W-scaled.width)//2,125+(460-scaled.height)//2))
        writer.send(np.asarray(current).tobytes())
writer.close()
print(OUT)
