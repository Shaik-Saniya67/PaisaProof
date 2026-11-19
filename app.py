import hashlib, json
import pandas as pd, streamlit as st, streamlit.components.v1 as components
from paisaproof import parse, audit as A, ai, report, samples, ui
from paisaproof.audit import hm

st.set_page_config(page_title="PaisaProof", page_icon="🧾", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)
if hasattr(st, "iframe"): st.iframe(ui.BG, height=1)
else: components.html(ui.BG, height=0)
NAV = ["Overview", "New audit", "Sample investigation", "Evaluation", "Privacy & limits"]
st.session_state.setdefault("nav", NAV[0])
go = lambda p: st.session_state.update(nav=p)
with st.sidebar:
    st.markdown("<div class=brand>PAISAPROOF<small>Transaction Evidence Lab</small></div>", unsafe_allow_html=True)
    st.radio("Navigate", NAV, key="nav", label_visibility="collapsed")
    st.caption("Demo workspace. Local session, nothing is stored.")
page = st.session_state.nav

def results(res, ctx):
    t1, t2, t3 = st.tabs(["Reconstruction", "Findings", "Complaint pack"])
    with t1:
        if hasattr(st, "iframe"): st.iframe(ui.recon(res), height=660)
        else: components.html(ui.recon(res), height=660, scrolling=False)
    with t2: st.markdown(ui.findings_html(res), unsafe_allow_html=True)
    with t3:
        k = f"cp_{ctx['id']}"
        if k not in st.session_state: st.session_state[k] = ai.complaint(res, ctx)
        l, r = st.columns([3, 2])
        txt = l.text_area("Complaint draft: review and edit before using it. PaisaProof never files anything.", key=k, height=420)
        ev = [e for f in res["findings"] for e in f["evidence"]]
        r.markdown("**Attached evidence**")
        for e in ev: r.markdown(f"<div class=ev><b>{e['source']}</b> {'✓' if e.get('verified') else '⚠'} {e['quote']}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.download_button("Download evidence report (PDF)", report.pdf(res, ctx, txt), "paisaproof_report.pdf", "application/pdf")
        c2.download_button("Download complaint text", txt, "complaint.txt")

def overview():
    st.markdown(ui.HERO, unsafe_allow_html=True)
    a, b, _ = st.columns([1.3, 1.5, 3])
    a.button("Start a transaction audit", type="primary", on_click=go, args=("New audit",))
    b.button("Explore a sample investigation", on_click=go, args=("Sample investigation",))
    st.markdown("### One transaction. Three records. One clear answer.")
    st.write("Receipt, bank SMS and bank statement are read, matched by reference and time, and checked by fixed rules. AI helps read messy text and word the complaint. It never decides the finding.")

def new_audit():
    st.markdown("<div class=steps><span class=on>1 Tell us what happened</span><span>2 Add evidence</span><span>3 Review what we read</span></div>", unsafe_allow_html=True)
    c = st.columns(3)
    req = c[0].number_input("Amount requested (₹)", 0.0, value=5000.0, step=100.0)
    recv = c[1].number_input("Cash you received (₹), customer reported", 0.0, value=4940.0, step=10.0)
    date = c[2].text_input("Transaction date", "18-11-2026")
    d = st.columns(2); bank = d[0].text_input("Bank or provider (optional)"); place = d[1].text_input("Location (optional)")
    st.caption("Cash received is what you remember. It stays marked customer reported unless other evidence supports it.")
    u = st.columns(3); T = {}; upload_errors = []
    for col, key, title, types in ((u[0], "Receipt", "01 Agent receipt", ["png", "jpg", "jpeg", "pdf"]), (u[1], "SMS", "02 Bank SMS", ["png", "jpg", "jpeg"]), (u[2], "Statement", "03 Bank statement", ["pdf", "csv", "txt", "png", "jpg"])):
        with col:
            st.markdown(f"**{title}**")
            f = st.file_uploader("File", type=types, key=f"f{key}", label_visibility="collapsed")
            t = st.text_area("or paste text", key=f"t{key}", height=110)
            if t.strip():
                T[key] = t.strip()
            elif f:
                extracted = parse.to_text(f.name, f.getvalue())
                T[key] = extracted
                if not extracted.strip():
                    upload_errors.append(f"{title}: file uploaded, but text could not be read. Paste the message text manually or check OCR/Tesseract installation.")
            else:
                T[key] = ""
    for msg in upload_errors:
        st.warning(msg)
    if st.button("Read my evidence", type="primary"):
        ex = dict(rc=parse.receipt(T["Receipt"]), sm=parse.sms(T["SMS"]), rows=parse.statement(T["Statement"]), texts=T)
        for r, k, f in ((ex["rc"], "Receipt", "cash"), (ex["sm"], "SMS", "debit")):
            if r and (r[f] is None or not r["ref"]):
                g = ai.extract(T[k], k)
                if r[f] is None and "amount" in g: r[f] = g["amount"]
                if not r["ref"] and "ref" in g: r["ref"] = g["ref"]
        st.session_state.ex = ex; st.session_state.pop("res", None)
    ex = st.session_state.get("ex")
    if not ex: return
    eid = hashlib.md5(json.dumps(ex["texts"]).encode()).hexdigest()[:8]
    st.markdown("<div class=steps><span>1</span><span>2</span><span class=on>3 Review what we read, correct anything uncertain</span></div>", unsafe_allow_html=True)
    rc, sm, a, b = ex["rc"], ex["sm"], *st.columns(2)
    if rc:
        with a:
            st.markdown("**Receipt**"); rc["cash"] = st.number_input("Cash recorded (₹)", value=rc["cash"], key=f"rc{eid}"); rc["fee"] = st.number_input("Printed charge (₹)", value=rc["fee"], key=f"rf{eid}")
            rc["ref"] = st.text_input("Reference", rc["ref"] or "", key=f"rr{eid}") or None; rc["failed"] = st.checkbox("Marked failed", rc["failed"], key=f"rx{eid}")
    if sm:
        with b:
            st.markdown("**Bank SMS**"); sm["debit"] = st.number_input("Debit (₹)", value=sm["debit"], key=f"sd{eid}"); sm["ref"] = st.text_input("Reference ", sm["ref"] or "", key=f"sr{eid}") or None
    rows = ex["rows"]; st.markdown("**Statement entries**")
    df = pd.DataFrame([{"amount": r["amount"], "dir": r["dir"], "ref": r["ref"] or "", "time": hm(r["time"]) or ""} for r in rows], columns=["amount", "dir", "ref", "time"])
    ed = st.data_editor(df, num_rows="dynamic", key=f"ed{eid}", column_config={"dir": st.column_config.SelectboxColumn(options=["DR", "CR"])})
    new = [dict(amount=float(r.amount), dir=r.dir or "DR", ref=r.ref or None, time=parse.tmin(str(r.time or "")), line=rows[i]["line"] if i < len(rows) else f"{r.amount} {r.dir} {r.ref}") for i, r in enumerate(ed.dropna(subset=["amount"]).itertuples())]
    if st.button("Run audit", type="primary"):
        ctx = dict(date=date, bank=bank, place=place, ref=(rc or {}).get("ref") or (sm or {}).get("ref"), id=hashlib.md5(json.dumps([req, recv, ex["texts"]]).encode()).hexdigest()[:8])
        st.session_state.res = (A.audit(req, recv, rc, sm, new, ex["texts"]), ctx)
    if "res" in st.session_state: results(*st.session_state.res)

def sample():
    st.markdown("<div class=steps><span class=on>Sample investigation</span><span>Synthetic records, expected result fixed in advance</span></div>", unsafe_allow_html=True)
    pick = st.selectbox("Choose a test scenario", [x["name"] for x in samples.CASES], index=1)
    c = next(x for x in samples.CASES if x["name"] == pick)
    res = samples.run(c); st.caption(f"Expected result for this case: {c['expect']}. All records are synthetic.")
    results(res, dict(date="18-11-2026", bank="Demo Bank", place="Sahara CSP (synthetic)", ref=c["truth"]["ref"], id="s" + hashlib.md5(c["name"].encode()).hexdigest()[:6]))

def evaluation():
    st.markdown("### Evaluation on 8 synthetic scenarios")
    rows, m = samples.evaluate(); k = st.columns(5)
    for col, (n, v) in zip(k, (("Status accuracy", m["status_accuracy"]), ("Field extraction", m["extraction_accuracy"]), ("Evidence verified", m["evidence_verified"]), ("Precision", m["precision"]), ("Recall", m["recall"]))): col.metric(n, f"{v:.0%}")
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.caption(f"Computed live from the code. False accusations on clean cases: {m['false_accusations']}. These 8 cases were written by us with the expected answers fixed first, so this shows the rules behave as designed. It is not a claim about accuracy on real documents.")

def privacy():
    st.markdown("### Privacy and limits")
    st.markdown("- The public demo uses synthetic records. Mask account numbers and personal details before using real documents.\n- Nothing is saved. Uploads live only in this session. Document text is sent to an AI service only when an API key is configured and only for reading or wording.\n- Records can show that amounts disagree. They cannot prove how much cash was handed over, so that figure stays customer reported.\n- PaisaProof is not an official bank verification service, gives no legal advice and never files a complaint for you.\n- OCR quality depends on photo quality. Always check the review step.")

{"Overview": overview, "New audit": new_audit, "Sample investigation": sample, "Evaluation": evaluation, "Privacy & limits": privacy}[page]()

# Render activity after the page logic so a Groq request made during this run is reflected immediately.
with st.sidebar:
    st.divider()
    st.markdown("### AI assistance")
    ai_state = ai.status()
    if ai_state["key_configured"]:
        st.markdown("🟢 **Groq key configured**")
        if ai_state["last_status"] == "success":
            st.caption(f"Last AI call succeeded · {ai_state['last_task']}")
        elif ai_state["last_status"] == "failed":
            st.warning(f"Last AI call failed ({ai_state['last_error']}). Check the key, model and network.")
        else:
            st.caption("No AI call yet. Rule-based extraction may not have needed the AI fallback.")
        st.caption(f"Model: `{ai_state['model']}` · Successful calls this session: {ai_state['successes']}")
    else:
        st.markdown("⚪ **Groq key not configured**")
        st.caption("Rule-based processing still works. Add GROQ_API_KEY to enable optional AI assistance.")
