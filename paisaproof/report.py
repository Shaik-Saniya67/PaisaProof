import io, datetime
from xml.sax.saxutils import escape as E
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
S = lambda x: E(str(x).replace("₹", "Rs."))
def pdf(res, ctx, text):
    b = ParagraphStyle("b", fontName="Times-Roman", fontSize=10.5, leading=14); h = ParagraphStyle("h", fontName="Times-Bold", fontSize=13, leading=16, spaceBefore=10, spaceAfter=3)
    t = ParagraphStyle("t", fontName="Times-Bold", fontSize=20, leading=24); m = ParagraphStyle("m", fontName="Courier", fontSize=8.5, leading=11, leftIndent=8)
    f = lambda v: "n/a" if v is None else f"Rs {v:,.2f}"
    st = [Paragraph("PaisaProof Evidence Report", t), Paragraph(f"Audit status: <b>{S(res['status'].replace('_', ' '))}</b>. Generated {datetime.date.today()}. Synthetic or customer-supplied records.", b), Spacer(1, 8)]
    tb = Table([["Requested", f(res["requested"])], ["Cash received (customer reported)", f(res["received"])], ["Account debit", f(res["debit"])], ["Unexplained difference", f(res["unexplained"])]], colWidths=[260, 140])
    tb.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Times-Roman"), ("FONTSIZE", (0, 0), (-1, -1), 10.5), ("GRID", (0, 0), (-1, -1), .4, colors.grey)])); st.append(tb)
    for x in res["findings"]:
        st += [Paragraph(f"{x['id']}. {S(x['title'])}" + (f" ({f(x['amount'])})" if x["amount"] is not None else ""), h), Paragraph(S(x["explanation"]), b)]
        st += [Paragraph(f"{S(e['source'])}{' (verified)' if e.get('verified') else ' (not verified)'}: {S(e['quote'])}", m) for e in x["evidence"]]
        st += [Paragraph("Still unknown: " + S(x["unknown"]), b), Paragraph("Next step: " + S(x["next_step"]), b)]
    st += [Paragraph("Complaint draft", h), Paragraph(S(text).replace("\n", "<br/>"), b), Spacer(1, 8),
           Paragraph("<i>PaisaProof compares records you provide. It is not an official bank verification and does not allege wrongdoing. Cash physically received is customer reported. Review and edit before use.</i>", b)]
    o = io.BytesIO(); SimpleDocTemplate(o, pagesize=A4, leftMargin=48, rightMargin=48, topMargin=44, bottomMargin=44).build(st); return o.getvalue()
