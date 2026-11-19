import json
import pathlib
from html import escape as H

BG = (pathlib.Path(__file__).parent / "bg.html").read_text(encoding="utf-8")

STATUS = {
    "matched": ("Records agree", "#3B9279"),
    "discrepancy": ("Needs investigation", "#D95D50"),
    "disclosed_charge": ("Disclosed charge", "#3B9279"),
    "potential_split": ("Possible split debit", "#E7A83E"),
    "duplicate": ("Possible duplicate debit", "#D95D50"),
    "reversal_identified": ("Reversal identified", "#3B9279"),
    "insufficient_evidence": ("Insufficient evidence", "#E7A83E"),
    "unmatched": ("Records do not match", "#E7A83E"),
}

SEV = {
    "ok": "#3B9279",
    "review": "#E7A83E",
    "alert": "#D95D50",
}

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@500&display=swap');

html, body {
    background: #02160c;
    scroll-behavior: smooth;
}

.stApp {
    background: transparent !important;
    color: #E4F3EA;
    font-family: Inter, system-ui, sans-serif;
}

.stApp > header,
header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stMain"],
[data-testid="stAppViewContainer"] {
    background: transparent !important;
    scroll-behavior: smooth;
}

[data-testid="stMainBlockContainer"],
.block-container {
    position: relative;
    z-index: 1;
}

h1, h2, h3, .brand {
    font-family: 'Space Grotesk', system-ui, sans-serif !important;
    letter-spacing: -.02em;
    color: #EAF7F0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(2,22,12,.88) !important;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-right: 1px solid rgba(52,232,154,.14);
    z-index: 2;
}

[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {
    background: transparent !important;
}

[data-testid="stSidebar"] * {
    color: #E4F3EA !important;
}

.brand {
    font-weight: 700;
    font-size: 19px;
    letter-spacing: .04em;
    padding: 6px 0 10px;
    color: #fff !important;
}

.brand small {
    display: block;
    font: 400 11px Inter;
    opacity: .7;
    letter-spacing: .02em;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: transform .25s, box-shadow .25s, background .25s;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(.98);
}

.stButton > button[kind="primary"],
.stDownloadButton > button {
    background: linear-gradient(135deg, #34e89a, #1fbf7a) !important;
    color: #02160c !important;
    border: 0 !important;
    box-shadow: 0 6px 22px rgba(52,232,154,.18);
}

.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    box-shadow: 0 10px 30px rgba(52,232,154,.30);
}

.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(52,232,154,.3) !important;
    color: #E4F3EA !important;
}

/* Sidebar navigation */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
    gap: 4px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 9px 12px;
    border-radius: 8px;
    width: 100%;
    cursor: pointer;
    border: 1px solid transparent;
    transition: background .25s, border-color .25s;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(52,232,154,.10) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(52,232,154,.14) !important;
    border-color: rgba(52,232,154,.38) !important;
}

/* Replace default red radio accent with emerald */
input[type="radio"] {
    accent-color: #34E89A !important;
}

[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
    border-color: #34E89A !important;
}

[data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) > div:first-child {
    border-color: #34E89A !important;
}

[data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) > div:first-child > div {
    background-color: #34E89A !important;
}

[data-testid="stRadio"] [role="radio"][aria-checked="true"] {
    border-color: #34E89A !important;
    color: #34E89A !important;
}

/* Tabs */
[data-testid="stTabs"] button {
    transition: color .25s, background .25s;
}

[data-testid="stTabs"] button[role="tab"] {
    color: #A9C4B5 !important;
}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #34E89A !important;
    border-bottom-color: #34E89A !important;
}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #34E89A !important;
}

/* Dark and readable text areas */
[data-testid="stTextArea"] textarea,
[data-baseweb="textarea"] textarea,
textarea {
    background: #0A261A !important;
    background-color: #0A261A !important;
    color: #E4F3EA !important;
    -webkit-text-fill-color: #E4F3EA !important;
    caret-color: #34E89A !important;
    border: 1px solid rgba(52,232,154,.30) !important;
    border-radius: 8px !important;
    opacity: 1 !important;
    text-shadow: none !important;
}

[data-testid="stTextArea"] > div,
[data-baseweb="textarea"] {
    background: #0A261A !important;
    border-radius: 8px !important;
}

[data-testid="stTextArea"] textarea::placeholder,
textarea::placeholder {
    color: #92AA9D !important;
    -webkit-text-fill-color: #92AA9D !important;
}

[data-testid="stTextArea"] textarea:focus,
textarea:focus {
    border-color: #34E89A !important;
    box-shadow: 0 0 0 1px #34E89A !important;
    outline: none !important;
}

/* Text inputs */
[data-testid="stTextInput"] input,
[data-baseweb="input"] input {
    background: #0A261A !important;
    color: #E4F3EA !important;
    -webkit-text-fill-color: #E4F3EA !important;
    border-color: rgba(52,232,154,.3) !important;
}

/* Dropdown */
[data-baseweb="select"] > div {
    border-color: rgba(52,232,154,.3) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(52,232,154,.14);
    border-radius: 10px;
    padding: 12px 14px;
}

/* Animations */
@keyframes ppIn {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: none;
    }
}

[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"],
[data-testid="stMainBlockContainer"] [data-testid="stTabs"] {
    animation: ppIn .55s cubic-bezier(.2,.8,.2,1) both;
}

[data-stale="true"] {
    opacity: .75 !important;
    transition: opacity .3s ease;
}

[data-testid="stMainBlockContainer"] .stMarkdown p,
[data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"],
.hero h1,
.hero p {
    text-shadow: 0 1px 8px rgba(2,22,12,.75);
}

.find *,
.find {
    text-shadow: none !important;
}

input, textarea, [data-baseweb="select"] > div {
    transition: border-color .25s, box-shadow .25s;
}

/* Hero */
.hero {
    display: grid;
    grid-template-columns: 1.1fr .9fr;
    gap: 32px;
    align-items: center;
    padding: 8px 0 24px;
}

.hero h1 {
    font-size: clamp(2.2rem,5vw,3.8rem);
    line-height: 1.04;
    margin: .1em 0;
}

.hero p {
    max-width: 50ch;
    color: #A9C4B5;
    font-size: 1.05rem;
}

/* Evidence cards */
.paper {
    position: relative;
    height: 300px;
    perspective: 900px;
}

.paper div {
    position: absolute;
    width: 210px;
    padding: 14px 16px;
    background: #fffdf7;
    border: 1px solid #e4dfd0;
    border-radius: 4px;
    box-shadow: 0 18px 40px #00000066;
    font: 500 12px 'IBM Plex Mono', monospace;
    color: #4a5568;
    transition: transform .5s;
}

.paper b {
    display: block;
    font: 700 26px 'Space Grotesk', sans-serif;
    color: #101C2C;
    margin-top: 4px;
}

.paper .a {
    left: 0;
    top: 6px;
    transform: rotateY(-14deg) rotate(-4deg);
}

.paper .b {
    left: 100px;
    top: 92px;
    transform: rotateY(-10deg) rotate(2deg);
}

.paper .c {
    left: 200px;
    top: 178px;
    transform: rotateY(-6deg) rotate(-1deg);
}

.paper:hover .a {
    transform: rotateY(-6deg) rotate(-6deg) translateX(-10px);
}

.paper:hover .c {
    transform: rotateY(-2deg) rotate(1deg) translateX(12px);
}

/* Findings */
.find {
    color: #101C2C;
    transition: transform .3s, box-shadow .3s;
    box-shadow: 0 8px 24px #00000040;
    background: #fffdf7;
    border: 1px solid #e4dfd0;
    border-left: 5px solid var(--c);
    border-radius: 4px;
    padding: 14px 16px;
    margin: 10px 0;
}

.find h4 {
    margin: 0 0 4px;
    font: 600 17px 'Space Grotesk', sans-serif;
}

.find .amt {
    font: 500 22px 'IBM Plex Mono', monospace;
    color: var(--c);
    float: right;
}

.pill {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 99px;
    background: var(--c);
    color: #fff;
}

.find:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 34px #00000059;
}

.ev {
    color: #101C2C;
    font: 12px 'IBM Plex Mono', monospace;
    background: #f0ece0;
    padding: 6px 8px;
    border-radius: 3px;
    margin: 4px 0;
    word-break: break-word;
}

.find small {
    color: #5b6472;
}

/* Progress steps */
.steps {
    display: flex;
    gap: 8px;
    margin: 6px 0 16px;
    flex-wrap: wrap;
}

.steps span {
    font: 600 12px Inter;
    padding: 4px 12px;
    border-radius: 99px;
    background: rgba(255,255,255,.08);
    color: #C9DDD0;
}

.steps .on {
    background: #34e89a;
    color: #02160c;
}

@media(max-width:800px) {
    .hero {
        grid-template-columns: 1fr;
    }
}

@media(prefers-reduced-motion:reduce) {
    * {
        transition: none !important;
        animation: none !important;
        scroll-behavior: auto !important;
    }
}
</style>"""

HERO = """<div class=hero>
<div>
<div class=steps><span class=on>Transaction Evidence Lab</span></div>
<h1>Where did your money go?</h1>
<p>Compare what you requested, what you received and what your bank recorded. One transaction, three records, one clear answer.</p>
</div>
<div class=paper>
<div class=a>RECEIPT<b>₹4,940</b>cash recorded</div>
<div class=b>BANK SMS<b>₹5,000</b>debit alert</div>
<div class=c>STATEMENT<b>₹5,000</b>account debit</div>
</div>
</div>"""


def findings_html(res):
    lab, col = STATUS[res["status"]]

    output = [
        f"<div class=find style='--c:{col}'>"
        f"<span class=pill style='--c:{col}'>{lab}</span> "
        "<small>Differences are not accusations. Each finding lists what is still unknown.</small>"
        "</div>"
    ]

    for finding in res["findings"]:
        color = SEV[finding["severity"]]
        amount = (
            f"<span class=amt>₹{finding['amount']:,.2f}</span>"
            if finding["amount"] is not None
            else ""
        )

        evidence = "".join(
            f"<div class=ev><b>{H(item['source'])}</b> "
            f"{'✓ verified in source' if item.get('verified') else '⚠ not found in source'}"
            f"<br>{H(item['quote'])}</div>"
            for item in finding["evidence"]
        )

        output.append(
            f"<div class=find style='--c:{color}'>"
            f"{amount}"
            f"<span class=pill style='--c:{color}'>{finding['id']}</span>"
            f"<h4>{H(finding['title'])}</h4>"
            f"<p>{H(finding['explanation'])}</p>"
            f"{evidence}"
            f"<small><b>Still unknown:</b> {H(finding['unknown'])}"
            f"<br><b>Next step:</b> {H(finding['next_step'])}</small>"
            "</div>"
        )

    return "".join(output)


def recon(res):
    lab, col = STATUS[res["status"]]

    data = dict(
        cards=res["cards"],
        req=res["requested"],
        recv=res["received"],
        debit=res["debit"],
        un=res["unexplained"],
        lab=lab,
        col=col,
        tl=res["timeline"],
        id="PP-DEMO",
    )

    return TPL.replace(
        "__DATA__",
        json.dumps(data).replace("</", "<\\/")
    )


TPL = r"""<!doctype html>
<meta charset=utf-8>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@500&display=swap" rel=stylesheet>
<style>
* {
    box-sizing: border-box;
    margin: 0;
}

body {
    background: #101C2C;
    color: #E9E6DD;
    font: 14px/1.5 Inter, system-ui, sans-serif;
    padding: 22px;
    border-radius: 8px;
}

h2 {
    font: 700 15px 'Space Grotesk', sans-serif;
    letter-spacing: .03em;
    color: #9fb0c8;
    font-weight: 500;
}

.cards {
    display: flex;
    align-items: stretch;
    justify-content: center;
    gap: 0;
    margin: 20px 0;
    perspective: 1100px;
}

.card {
    width: 220px;
    background: #F5F2EA;
    color: #101C2C;
    border-radius: 4px;
    padding: 16px;
    transition: transform .35s, box-shadow .35s;
    box-shadow: 0 14px 30px #0008;
    transform: translateZ(calc(var(--d)*14px));
}

.card small {
    font-weight: 600;
    color: #5b6472;
}

.card b {
    display: block;
    font: 700 34px 'IBM Plex Mono', monospace;
    margin: 4px 0;
}

.card span {
    color: #5b6472;
    font-size: 12px;
}

.card i {
    display: block;
    margin-top: 10px;
    font: 11px 'IBM Plex Mono', monospace;
    color: #44505f;
    background: #e9e4d6;
    padding: 5px 7px;
    border-radius: 3px;
    font-style: normal;
    word-break: break-word;
}

.cn {
    width: 58px;
    align-self: center;
    height: 4px;
    border-radius: 9px;
    background: repeating-linear-gradient(
        90deg,
        var(--c) 0 8px,
        transparent 8px 14px
    );
    background-size: 28px 4px;
    animation: mv 1.2s linear infinite;
}

@keyframes mv {
    to {
        background-position: 28px 0;
    }
}

.spot {
    text-align: center;
    padding: 14px 0 8px;
}

.spot .big {
    font: 700 64px/1 'Space Grotesk', sans-serif;
    color: var(--c);
    transition: transform .6s;
}

.spot p {
    color: #9fb0c8;
}

.pill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 99px;
    background: var(--c);
    color: #101C2C;
    font-weight: 700;
    font-size: 12px;
    margin-bottom: 8px;
}

.facts {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
    margin: 10px 0 14px;
}

.facts div {
    background: #1b2b42;
    border-radius: 6px;
    padding: 8px 14px;
}

.facts b {
    display: block;
    font: 500 17px 'IBM Plex Mono', monospace;
}

.facts small {
    color: #9fb0c8;
}

.tl {
    display: flex;
    gap: 18px;
    flex-wrap: wrap;
    justify-content: center;
    font-size: 13px;
    color: #c9d3e2;
}

.tl b {
    font-family: 'IBM Plex Mono', monospace;
    color: #fff;
}

@media(max-width:700px) {
    .cards {
        flex-direction: column;
        align-items: center;
    }

    .cn {
        width: 4px;
        height: 30px;
    }
}

@media(prefers-reduced-motion:reduce) {
    * {
        animation: none !important;
        transition: none !important;
    }
}
</style>

<h2>TRANSACTION RECONSTRUCTION · illustrative or customer-supplied records</h2>
<div class=cards id=cards></div>

<div class=spot style="--c:__C__">
    <div class=pill id=lab></div>
    <div class=big id=big></div>
    <p>Difference requiring explanation. Review required, not proof of wrongdoing.</p>
</div>

<div class=facts id=facts></div>
<div class=tl id=tl></div>

<script>
const D = __DATA__;
const $ = s => document.getElementById(s);

const f = v => v == null
    ? "n/a"
    : "₹" + v.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

const esc = s => String(s ?? "").replace(/[&<>]/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;"
}[c]));

document.querySelector(".spot").style.setProperty("--c", D.col);
$("lab").textContent = D.lab;
$("lab").parentElement.style.setProperty("--c", D.col);

let html = "";

D.cards.forEach((c, i) => {
    if (i) {
        const a = D.cards[i-1].v;
        const b = c.v;

        const color = a == null || b == null
            ? "#E7A83E"
            : Math.abs(a-b) < .01
                ? "#3B9279"
                : "#D95D50";

        html += `<div class=cn style="--c:${color}"></div>`;
    }

    html += `
        <div class=card style="--d:${i}">
            <small>${esc(c.label)}</small>
            <b>${f(c.v)}</b>
            <span>${esc(c.sub)}</span>
            ${c.q ? `<i>${esc(c.q)}</i>` : ""}
        </div>`;
});

$("cards").innerHTML = html;

document.querySelectorAll(".card").forEach(el => {
    el.onmousemove = e => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX-r.left)/r.width-.5;
        const y = (e.clientY-r.top)/r.height-.5;

        el.style.transform =
            `translateZ(30px) rotateY(${x*12}deg) rotateX(${-y*10}deg)`;

        el.style.boxShadow = "0 26px 44px #000a";
    };

    el.onmouseleave = () => {
        el.style.transform = "";
        el.style.boxShadow = "";
    };
});

$("facts").innerHTML = `
    <div><small>Requested</small><b>${f(D.req)}</b></div>
    <div><small>Reported cash received</small><b>${f(D.recv)}</b></div>
    <div><small>Bank debit</small><b>${f(D.debit)}</b></div>
`;

$("tl").innerHTML = D.tl.map(t =>
    `<span><b>${t.t}</b> ${esc(t.e)}</span>`
).join("") || "No timestamps found in the records.";

const t0 = performance.now();
const duration = 900;

const tick = n => {
    const p = Math.min(1, (n-t0)/duration);
    $("big").textContent = f(D.un * (1-Math.pow(1-p,3)));

    if (p < 1) requestAnimationFrame(tick);
};

requestAnimationFrame(tick);
</script>
""".replace("__C__", "#D95D50")
