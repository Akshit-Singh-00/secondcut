"""Generate the technical report and print-accurate calibration mat."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'pdf'; OUT.mkdir(parents=True,exist_ok=True)
evaluation=json.loads((ROOT/'artifacts'/'evaluation.json').read_text())
ink=colors.HexColor('#203b32'); green=colors.HexColor('#69855d'); orange=colors.HexColor('#db643b'); light=colors.HexColor('#eff2e8')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('SCBody',fontName='Helvetica',fontSize=10,leading=15,textColor=ink,spaceAfter=10))
styles.add(ParagraphStyle('SCTitle',fontName='Helvetica-Bold',fontSize=34,leading=39,textColor=ink,spaceAfter=16))
styles.add(ParagraphStyle('SCHead',fontName='Helvetica-Bold',fontSize=17,leading=22,textColor=ink,spaceBefore=13,spaceAfter=12))
styles.add(ParagraphStyle('SCEye',fontName='Helvetica-Bold',fontSize=9,leading=12,textColor=orange,spaceAfter=14))
styles.add(ParagraphStyle('SCSmall',fontName='Helvetica',fontSize=8,leading=11,textColor=ink,spaceAfter=8))
story=[]
def p(text,style='SCBody'):story.append(Paragraph(text,styles[style]))
def h(text):p(text,'SCHead')
def table(rows,widths):
    t=Table([[Paragraph(str(c),styles['SCSmall']) for c in row] for row in rows],colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d9dfd2'))]))
    story.append(t)
def page():story.append(PageBreak())
def footer(c,doc):
    c.setStrokeColor(colors.HexColor('#d9dfd2'));c.line(20*mm,18*mm,190*mm,18*mm)
    c.setFont('Helvetica',8);c.setFillColor(green);c.drawString(20*mm,12*mm,'SECONDCUT | Technical report | 7 October 2026');c.drawRightString(190*mm,12*mm,str(doc.page))

p('OPENCV AI COMPETITION 2026 / REVIEW DRAFT','SCEye')
p('SecondCut','SCTitle')
p('A wrong cut. A workable next step.','SCHead')
p('A camera-guided recovery prototype for a two-panel cardboard organizer insert. It measures the material that remains, finds feasible rectangular blanks, propagates shared slot dimensions, and checks a new capture against the accepted plan.')
table([['Evidence status','What is established'],['Implemented and tested','OpenCV 5.0.0 perception; bounded geometric planner; approval-gated SVG; recapture verification; local web interface.'],['Synthetic evaluation',f"{evaluation['passed']}/{evaluation['total']} generated scenarios produce the expected workflow outcome. Automated tests additionally cover geometry, approval, invalid inputs, and slot verification."],['Not yet established','Real cardboard dimensional accuracy and assembly fit; deployed AWS endpoint; cloud performance; participant introduction video.']], [43*mm,127*mm])
h('Problem and intended users')
p('A novice maker can lose a project after trimming a panel too short, removing a corner, or cutting a notch too deeply. SecondCut explores whether the remaining material can still support a smaller, compatible design. Intended users are hobby makers, educators, and small craft workshops working with simple sheet material.')
h('Scope')
p('One flat, matte brown cardboard blank on an A4 marker mat. One parameterized cross-slot insert, with a second panel cut from separate stock. The insert has no base or exterior walls. This prototype does not reconstruct arbitrary CAD, compensate for warped material, predict strength, or operate cutting equipment.')
page()
p('01 / SYSTEM DESIGN','SCEye');h('From evidence to a revised plan')
table([['Stage','Implementation and output'],['Capture','PNG/JPEG input or a clearly labeled synthetic sample. Four ArUco markers establish a known planar scale.'],['Perception','OpenCV 5 detects markers, computes a homography, rectifies the image, segments contrasting material, checks edge quality, and preserves holes.'],['Planning','A 1 mm occupancy grid is eroded by a 2 mm edge allowance. A histogram-based rectangle search finds candidate dimensions bounded by original and minimum dimensions. Dominated options are removed.'],['Shared constraints','The main panel and companion share the selected height. Each slot reaches half that height; both use the entered material thickness.'],['Human decision','Export stays locked until a user accepts an option. The companion requires separate stock and the footprint may shrink.'],['Verification','A new photo is checked for dimensions, silhouette overlap, and an open top slot. A geometry match does not certify physical assembly.']], [35*mm,135*mm])
h('Architecture: implemented locally, prepared for AWS')
p('Browser upload / sample &gt; FastAPI &gt; OpenCV 5 tools &gt; bounded recovery solver &gt; human approval &gt; SVG template &gt; recaptured geometry check. See the separate architecture.svg for the component diagram.')
p('Local: Uvicorn and SQLite. Prepared cloud architecture: HTTPS Lambda function URL, application authentication, Python container with OpenCV 5 and Mangum, private S3 evidence storage, and CloudWatch execution logs. AWS deployment is pending account access and authorization; the presence of infrastructure code is not deployment evidence.')
h('Workflow autonomy')
p('This build uses a deterministic tool controller, not an LLM. Missing markers or weak measurements trigger recapture. Insufficient material triggers replacement. A feasible plan triggers human review. Visual results therefore select subsequent tools and actions. No claim of Agentic Vision award eligibility or COOL use is made in this draft.')
page()
p('02 / EVALUATION','SCEye');h('A reproducible software baseline')
p('Run <font face="Courier">python -m pytest -q</font> and <font face="Courier">python scripts/evaluate.py</font>. The evaluation images are generated from known dimensions and are not independent real-world test data. Local timing includes fixture generation; it is not AWS latency.')
rows=[['Generated scenario','Expected outcome','Observed outcome','Time (ms)']]
for r in evaluation['results']:
    rows.append([r['sample'],r['expected'],r['actual'],r['elapsed_ms']])
table(rows,[50*mm,43*mm,43*mm,34*mm])
p(f"Environment: OpenCV {escape(evaluation['opencv'])}; Python {escape(evaluation['python'])}; {escape(evaluation['platform'])}.",'SCSmall')
h('Meaningful failure checks')
p('Tests verify that proposed rectangles stay inside eroded material, a missing marker blocks planning, an undersized blank produces no repair, internal holes remain excluded, and a panel without the required slot fails verification. On small seeded random masks, the rectangle solver is compared against exhaustive search.')
h('Physical validation still required')
p('Print and measure the calibration mat; capture known cardboard dimensions under multiple angles and lighting conditions; compare measurements against a ruler; perform all three damage types; cut both panels; and record whether the slots assemble. Report dimensional error and successful assembly separately from synthetic software outcomes. Measure discarded material against replacing the affected panel, including any extra companion material.')
page()
p('03 / LIMITATIONS AND REPRODUCIBILITY','SCEye');h('Limits that affect the result')
p('The color threshold assumes matte brown or colored cardboard against white. Shadows, printed graphics, pale cardboard, glare, occlusion, or a curled mat may invalidate the segmentation. Align the blank with the mat axes; arbitrary part rotation is not supported. Four markers do not prove that the surface is planar or printed at the correct scale.')
p('A 2 mm edge allowance is an engineering margin, not a calibrated confidence interval. Verification thresholds (+/-3 mm dimensions, at least 94% silhouette overlap, and at least 75% slot clearance) are provisional and have not been validated on real cuts. Material thickness is entered manually. Slot friction, compression, and cutting kerf are not modeled.')
h('Responsible operation')
p('The user reviews the proposed footprint and approves the plan before export. No cutting machine is controlled. Images are not sent to a model provider. Local evidence is stored in SQLite. The prepared AWS configuration uses a private encrypted S3 bucket, 30-day object expiry, a shared judge password, bounded concurrency, and seven-day execution-log retention. Authentication and storage must be verified after deployment. Concurrency is not a spending cap.')
h('Reproduction and assets')
p('The repository includes source, exact observed dependency versions, generated fixtures, tests, evaluation JSON, an A4 mat, an SVG generator, a field guide, and an AWS SAM container template. The README provides local commands; infra/README.md describes deployment and its currently unverified steps. Demo fixtures and illustrations are authored for this project; no external dataset or trained weights are used.')
h('Related work and originality')
p('scrAPP already captures scrap contours with a smartphone and places CAD models. Fabricaide provides material-aware design and part placement. SecondCut explores a narrower repair loop after a cutting error, with shared slot constraints and recapture verification. We do not claim a world-first algorithm or patent novelty.')
p('scrAPP: https://pure.au.dk/portal/en/publications/scrapp-enabling-reuse-of-scrap-materials-with-a-smartphone/','SCSmall')
p('Fabricaide: https://hcie.csail.mit.edu/research/fabricaide/fabricaide.html','SCSmall')
p('Competition requirements: https://opencv26.devpost.com/','SCSmall')
p('Final readiness: AWS deployment, real-material validation, participant/team introduction, hosted demo video, and user review remain pending. Do not submit this draft as a completed cloud deployment.','SCSmall')
SimpleDocTemplate(str(OUT/'secondcut-technical-report.pdf'),pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=20*mm,bottomMargin=25*mm).build(story,onFirstPage=footer,onLaterPages=footer)

# Use the lossless generated image at its exact A4 dimensions.
mat_image=ROOT/'artifacts'/'calibration-mat.png'
if mat_image.exists():
    c=canvas.Canvas(str(OUT/'secondcut-calibration-mat.pdf'),pagesize=A4)
    c.drawImage(str(mat_image),0,0,width=210*mm,height=297*mm)
    c.setFillColor(ink);c.setFont('Helvetica',7)
    c.drawCentredString(105*mm,269*mm,'SecondCut | Print actual size | Marker centers: 180 mm horizontal / 267 mm vertical')
    c.save()
print(OUT)
