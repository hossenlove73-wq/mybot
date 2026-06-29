import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
from config import PDF_OUTPUT_DIR

os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

BLUE  = colors.HexColor("#1A3C5E")
ORANGE= colors.HexColor("#E67E22")
GREY  = colors.HexColor("#F5F6FA")
MGREY = colors.HexColor("#BDC3C7")
WHITE = colors.white

SKEL = {"RC": "Reinforced Concrete | بتن مسلح", "STEEL": "Steel Frame | اسکلت فلزی", "LBM": "Masonry | دیوار باربر"}
USE  = {"RESIDENTIAL": "Residential | مسکونی", "COMMERCIAL": "Commercial | تجاری", "OFFICE": "Office | اداری"}


def make_pdf(uid, rec):
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"{PDF_OUTPUT_DIR}/report_{uid}_{ts}.pdf"
    doc = SimpleDocTemplate(out, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm,  bottomMargin=2*cm)
    S = []
    h1 = ParagraphStyle("h1", fontSize=18, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("h2", fontSize=9,  textColor=MGREY, alignment=TA_CENTER, fontName="Helvetica")

    hdr = Table([[Paragraph("Construction Material Estimate", h1)],
                 [Paragraph("گزارش برآورد مصالح ساختمانی — مبحث مقررات ملی ایران", h2)]],
                colWidths=[17*cm])
    hdr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BLUE),
                              ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14)]))
    S.append(hdr)
    S.append(Spacer(1, 0.5*cm))

    r   = rec.get("result", {})
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lb  = ParagraphStyle("lb", fontSize=9, fontName="Helvetica-Bold", textColor=BLUE)
    vl  = ParagraphStyle("vl", fontSize=9, fontName="Helvetica")

    info = [
        ["Date / تاریخ",          now],
        ["Skeleton / اسکلت",      SKEL.get(rec.get("skeleton",""), "")],
        ["Usage / کاربری",        USE.get(rec.get("usage",""), "")],
        ["Floor Area / مساحت طبقه", f"{rec.get('floor_area',0):,.0f} m²"],
        ["Floors / طبقات",        str(rec.get("floors",0))],
        ["Total Area / زیربنا",   f"{r.get('total_area',0):,.0f} m²"],
    ]
    it = Table([[Paragraph(a, lb), Paragraph(b, vl)] for a,b in info], colWidths=[6*cm,11*cm])
    it.setStyle(TableStyle([("ROWBACKGROUNDS",(0,0),(-1,-1),[GREY,WHITE]),
                             ("BOTTOMPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),7),
                             ("LEFTPADDING",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.3,MGREY)]))
    S += [it, Spacer(1,0.4*cm), HRFlowable(width="100%",thickness=1.5,color=ORANGE), Spacer(1,0.4*cm)]

    sec = ParagraphStyle("sec", fontSize=12, fontName="Helvetica-Bold", textColor=BLUE)
    S.append(Paragraph("Material Quantities & Cost  |  مقادیر مصالح و هزینه", sec))
    S.append(Spacer(1, 0.25*cm))

    rows = [["Material / مصالح", "Quantity / مقدار", "Unit", "Cost (USD)"]]
    rows += [
        ["Concrete / بتن",      f"{r.get('concrete',0):,.1f}",  "m³",        f"${r.get('cost_concrete',0):,.0f}"],
        ["Cement / سیمان",      f"{r.get('cement',0):,.0f}",    "bags 50kg", f"${r.get('cost_cement',0):,.0f}"],
        ["Rebar / میلگرد",      f"{r.get('rebar_ton',0):,.2f}", "ton",       f"${r.get('cost_rebar',0):,.0f}"],
        ["Sand / ماسه",         f"{r.get('sand',0):,.1f}",      "m³",        f"${r.get('cost_sand',0):,.0f}"],
        ["Bricks / آجر",        f"{r.get('bricks',0):,}",       "pcs",       f"${r.get('cost_bricks',0):,.0f}"],
    ]
    mt = Table(rows, colWidths=[5.5*cm,3.5*cm,3*cm,5*cm])
    mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BLUE),("TEXTCOLOR",(0,0),(-1,0),WHITE),
                             ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
                             ("ROWBACKGROUNDS",(0,1),(-1,-1),[GREY,WHITE]),
                             ("ALIGN",(1,0),(-1,-1),"CENTER"),
                             ("BOTTOMPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),7),
                             ("GRID",(0,0),(-1,-1),0.3,MGREY)]))
    S += [mt, Spacer(1,0.4*cm), HRFlowable(width="100%",thickness=2,color=ORANGE), Spacer(1,0.3*cm)]

    tot = ParagraphStyle("tot", fontSize=15, textColor=ORANGE, fontName="Helvetica-Bold", alignment=TA_CENTER)
    S.append(Paragraph(f"Total Material Cost  |  هزینه کل مصالح<br/><b>${r.get('total_cost',0):,.0f} USD</b>", tot))
    S.append(Spacer(1,0.4*cm))

    nt = ParagraphStyle("nt", fontSize=7.5, textColor=colors.grey, alignment=TA_CENTER, fontName="Helvetica-Oblique")
    S.append(Paragraph("All quantities include 5% waste factor per Mabhas Iranian Building Regulations. "
                        "مقادیر شامل ۵٪ ضریب اتلاف طبق مبحث مقررات ملی ساختمان ایران می‌باشد.", nt))
    doc.build(S)
    return out
