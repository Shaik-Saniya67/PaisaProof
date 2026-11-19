"""Transaction matching + deterministic audit rules + evidence verification. No AI decides anything here."""
import re
from collections import Counter
from . import parse
N = lambda s: re.sub(r"\s+", " ", str(s)).strip().lower()
def hm(m): return None if m is None else f"{m // 60:02d}:{m % 60:02d}"
def Q(r, *k):
    for x in k:
        if (r.get("q") or {}).get(x): return r["q"][x]
    return (r.get("text") or "").strip().splitlines()[0] if r.get("text") else ""

def audit(requested, received, rc, sm, rows, texts):
    F, debits, credits = [], [], []
    E = lambda s, q: {"source": s, "quote": q}
    def add(title, amt, sev, why, ev, unk, nxt):
        F.append(dict(id=f"F{len(F) + 1:02d}", title=title, amount=amt, severity=sev, explanation=why,
                      evidence=[e for e in ev if e["quote"]], unknown=unk, next_step=nxt))
    def done(status, un=0.0):
        for f in F:
            for e in f["evidence"]: e["verified"] = N(e["quote"]) in N(texts.get(e["source"], ""))
        tl = sorted([(rc.get("time"), "Receipt generated")] if rc else [] , key=lambda x: x[0] or 0)
        ev = ([(rc.get("time"), "Receipt generated")] if rc else []) + ([(sm.get("time"), "Bank debit alert received")] if sm else []) \
             + [(r["time"], "Statement debit entry") for r in debits] + [(r["time"], "Reversal credited") for r in credits]
        tl = [dict(t=hm(t), e=e) for t, e in sorted(ev, key=lambda x: (x[0] is None, x[0] or 0)) if t is not None]
        ds = round(sum(r["amount"] for r in debits), 2)
        cards = [dict(label="Receipt", v=(rc or {}).get("cash"), sub="Cash recorded", q=Q(rc, "cash") if rc else ""),
                 dict(label="SMS", v=(sm or {}).get("debit"), sub="Debit alert", q=Q(sm, "cash") if sm else ""),
                 dict(label="Statement", v=ds if debits else None, sub="Account debit", q="; ".join(r["line"] for r in debits)[:120])]
        return dict(status=status, unexplained=round(un, 2), requested=requested, received=received, debit=ds if debits else None,
                    findings=F, cards=cards, timeline=tl)
    miss = [n for n, x in (("receipt", rc), ("SMS", sm), ("statement", rows)) if not x]
    if miss:
        add("Not enough evidence", None, "review", f"Missing: {', '.join(miss)}. A conclusion needs all three records.", [], "Whether the records agree.", "Add the missing record and run the audit again.")
        return done("insufficient_evidence")
    if rc.get("ref") and sm.get("ref") and rc["ref"] != sm["ref"]:
        add("Records may belong to different transactions", None, "review", f"The receipt shows reference {rc['ref']} but the SMS shows {sm['ref']}, so no amounts are compared.",
            [E("Receipt", Q(rc, "ref")), E("SMS", Q(sm, "ref"))], "Which records belong to this withdrawal.", "Check the reference numbers and upload the matching records.")
        return done("unmatched")
    ok = lambda r: (rc.get("ref") and r["ref"] == rc["ref"]) or (rc.get("time") is not None and r["time"] is not None and abs(r["time"] - rc["time"]) <= 10 and r["dir"] == "DR")
    debits[:] = [r for r in rows if r["dir"] == "DR" and ok(r)]
    credits[:] = [r for r in rows if r["dir"] == "CR" and rc.get("ref") and r["ref"] == rc["ref"]]
    ds, cs = round(sum(r["amount"] for r in debits), 2), round(sum(r["amount"] for r in credits), 2)
    L = lambda rs: [E("Statement", r["line"]) for r in rs]
    failed = rc.get("failed") or sm.get("failed")
    if not debits:
        add("No matching statement entry", None, "review", "The statement has no debit that matches this receipt by reference or time.", [E("Receipt", Q(rc, "ref"))], "Whether the account was debited.", "Check the statement period or add the right page.")
        return done("insufficient_evidence")
    if failed:
        if credits and cs >= ds - .01:
            add("Failed withdrawal was reversed", ds, "ok", f"The withdrawal failed, the account was debited Rs {ds:,.2f} and the same amount was credited back.", L(debits + credits), "Nothing outstanding in the records.", "Keep these records.")
            return done("reversal_identified")
        add("Debit for a failed withdrawal is not reversed", ds - cs, "alert", f"The records show a failed withdrawal but Rs {ds - cs:,.2f} has no matching reversal credit.", [E("Receipt", Q(rc, "ref"))] + L(debits), "Whether a reversal is still pending.", "Ask the bank for the reversal status of this reference.")
        return done("discrepancy", ds - cs)
    dup = [k for k, n in Counter((r["amount"], r["ref"]) for r in debits).items() if n > 1]
    if dup:
        amt, n = dup[0][0], Counter((r["amount"], r["ref"]) for r in debits)[dup[0]]
        add("Possible duplicate debit", amt * (n - 1), "alert", f"The same debit of Rs {amt:,.2f} with the same reference appears {n} times.", L([r for r in debits if r["amount"] == amt]), "Whether the bank recorded one withdrawal twice.", "Ask the bank to explain the repeated entry.")
        return done("duplicate", amt * (n - 1))
    if len(debits) > 1 and len({r["amount"] for r in debits}) > 1 and ds >= requested - .01:
        add("Several debits for one withdrawal", max(ds - requested, 0), "review", f"{len(debits)} debits totalling Rs {ds:,.2f} fall within minutes of this withdrawal.", L(debits), "Whether these debits are one transaction split in parts.", "Confirm with the bank that these entries belong to one withdrawal.")
        return done("potential_split", max(ds - requested, 0))
    fee = rc.get("fee") or sm.get("fee") or 0.0
    gap = round(ds - received - fee, 2)
    if rc.get("cash") is not None and abs(rc["cash"] - received) > .01:
        add("Receipt cash differs from what you reported", abs(rc["cash"] - received), "review", f"You reported Rs {received:,.2f} but the receipt records Rs {rc['cash']:,.2f}.", [E("Receipt", Q(rc, "cash"))], "Which cash amount is right.", "Re-check the receipt and your recollection.")
    if gap > .009:
        add("Cash amount discrepancy", gap, "alert", f"You reported receiving Rs {received:,.2f}, the account was debited Rs {ds:,.2f}, and no disclosed charge explains the Rs {gap:,.2f} difference in the submitted evidence.",
            [E("Receipt", Q(rc, "cash")), E("SMS", Q(sm, "cash"))] + L(debits), "Whether a permitted charge applies. The cash you received is your own report, not proven by these records.", "Ask the bank or agent to explain this difference in writing.")
        return done("discrepancy", gap)
    if fee > 0 and abs(gap) < .01:
        add("A disclosed charge explains the difference", fee, "ok", f"The difference of Rs {fee:,.2f} matches a charge printed on the records.", [E("Receipt", Q(rc, "fee"))] + L(debits), "Whether the charge is permitted for this service.", "Check the bank's published charges for this service.")
        return done("disclosed_charge")
    if abs(ds - requested) < .01 and abs(received - requested) < .01:
        add("All three records agree", requested, "ok", f"Requested, received and debited amounts are all Rs {requested:,.2f}.", [E("Receipt", Q(rc, "cash")), E("SMS", Q(sm, "cash"))] + L(debits), "Nothing outstanding.", "Keep these records.")
        return done("matched")
    add("Debit differs from the requested amount", abs(ds - requested), "review", f"You requested Rs {requested:,.2f} but the debit is Rs {ds:,.2f}.", [E("SMS", Q(sm, "cash"))] + L(debits), "Why the amounts differ.", "Ask the bank to explain the difference.")
    return done("discrepancy", abs(ds - requested))

def run(requested, received, receipt_text, sms_text, stmt_text):
    rc, sm, rows = parse.receipt(receipt_text), parse.sms(sms_text), parse.statement(stmt_text)
    res = audit(requested, received, rc, sm, rows, {"Receipt": receipt_text, "SMS": sms_text, "Statement": stmt_text})
    res.update(rc=rc, sm=sm, rows=rows)
    return res
