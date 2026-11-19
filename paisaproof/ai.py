"""AI assists with reading and wording only. Every number it returns is checked against the verified facts."""
import os, re, json, requests
from dotenv import load_dotenv

# Load local development secrets from .env. Render should use dashboard environment variables.
load_dotenv()

# In-memory diagnostics for this running app process; never store or expose the API key.
_ACTIVITY = {"calls": 0, "successes": 0, "failures": 0,
             "last_task": None, "last_status": "not_called", "last_error": None}

def status():
    """Return safe Groq configuration/activity details for the UI."""
    return {
        "key_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        **_ACTIVITY,
    }
def _groq(system, user, js=False, task="AI request"):
    k = os.getenv("GROQ_API_KEY")
    if not k:
        return None
    _ACTIVITY["calls"] += 1
    _ACTIVITY["last_task"] = task
    _ACTIVITY["last_error"] = None
    try:
        body = {"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), "temperature": 0.1, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if js: body["response_format"] = {"type": "json_object"}
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {k}"}, json=body, timeout=45)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        _ACTIVITY["successes"] += 1
        _ACTIVITY["last_status"] = "success"
        return content
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else None
        _ACTIVITY["failures"] += 1
        _ACTIVITY["last_status"] = "failed"
        _ACTIVITY["last_error"] = f"HTTP {code}" if code else "HTTP error"
        return None
    except Exception as exc:
        _ACTIVITY["failures"] += 1
        _ACTIVITY["last_status"] = "failed"
        _ACTIVITY["last_error"] = type(exc).__name__
        return None
nums = lambda s: {x.rstrip(".").replace(",", "") for x in re.findall(r"\d[\d,]*\.?\d*", s)}
def extract(text, kind):
    """AI fallback when rules miss a field. A value is kept only if it literally appears in the source text."""
    out = _groq(f'Extract from this {kind} text JSON {{"amount":number|null,"ref":string|null}}: the cash/debit amount and the transaction reference. Use null if absent. Never guess.', text, True, task=f'{kind} extraction')
    try: d = json.loads(out)
    except Exception: return {}
    res = {}
    if d.get("amount") is not None and str(d["amount"]).rstrip("0").rstrip(".") in nums(text) | {x.split(".")[0] for x in nums(text)}: res["amount"] = float(d["amount"])
    if d.get("ref") and str(d["ref"]) in text: res["ref"] = str(d["ref"])
    return res
def template(res, ctx):
    st = res["status"]
    if st in ("matched", "disclosed_charge", "reversal_identified"): return f"No complaint is drafted. {res['findings'][0]['title']}: the records agree or the difference is explained."
    if st in ("unmatched", "insufficient_evidence"): return "A complaint draft needs three matching records. Add the missing or matching records and run the audit again."
    ev = "\n".join(f"- {e['source']}: {e['quote']}" for f in res["findings"] for e in f["evidence"] if e.get("verified"))
    d = f"Rs {res['debit']:,.2f}" if res.get("debit") is not None else "[amount not available]"
    return (f"To,\nThe Grievance Redressal Officer\n{ctx.get('bank') or '[Bank / service provider]'}\n\n"
            f"Subject: Unexplained difference of Rs {res['unexplained']:,.2f} in a cash withdrawal through a banking agent (Ref {ctx.get('ref') or '[reference]'})\n\n"
            f"On {ctx.get('date')} I requested a cash withdrawal of Rs {res['requested']:,.2f}{(' at ' + ctx['place']) if ctx.get('place') else ''}. I received Rs {res['received']:,.2f}. "
            f"My account shows a debit of {d}. {res['findings'][0]['explanation']}\n\nSupporting records:\n{ev}\n\n"
            "Please explain this difference in writing and, if no valid charge applies, correct it.\n\nName: [your name]\nAccount (last 4 digits): [xxxx]\nMobile: [number]")
def complaint(res, ctx):
    base = template(res, ctx)
    if res["status"] not in ("discrepancy", "duplicate", "potential_split"): return base
    out = _groq("Rewrite this complaint more clearly and politely. Do not add, remove or change any fact, number, date or reference. Do not allege fraud or theft. Keep the placeholders in square brackets.", base, task="Complaint wording")
    return out.strip() if out and nums(out) <= nums(base) else base
