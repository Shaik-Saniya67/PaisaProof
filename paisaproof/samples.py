"""Eight synthetic cases (written by us, expected result fixed first) and a live evaluation runner."""
from . import audit as A, parse
def R(cash="5,000.00", fee=None, status="SUCCESS", ref="4412907781"):
    return f"SAHARA CSP - Cash Withdrawal\nDate 18-11-2026 10:42\nRef No: {ref}\nAmount requested Rs 5,000.00\n" + (f"Service charge Rs {fee}\n" if fee else "") + f"Cash paid Rs {cash}\nStatus: {status}"
def S(amt="5,000.00", ref="4412907781"): return f"Rs {amt} debited from A/c XX4821 on 18-11-2026 10:43 for CSP WDL Ref {ref}."
def L(amt="5,000.00", dr="DR", ref="4412907781", t="10:43", d="CSP-WDL"): return f"18-11-2026 {t} {d} {ref} {dr} {amt} BAL 12,340.00"
def C(name, recv, rc, sm, st, expect, cash, debit, ref="4412907781"):
    return dict(name=name, req=5000.0, recv=recv, receipt=rc, sms=sm, stmt=st, expect=expect, truth=dict(cash=cash, debit=debit, ref=ref))
CASES = [
 C("All three records match", 5000.0, R(), S(), L(), "matched", 5000.0, 5000.0),
 C("Cash shortfall of Rs 60", 4940.0, R("4,940.00"), S(), L(), "discrepancy", 4940.0, 5000.0),
 C("Clearly disclosed fee", 4950.0, R("4,950.00", "50.00"), S(), L(), "disclosed_charge", 4950.0, 5000.0),
 C("Two related debit entries", 5000.0, R(), S("3,000.00"), L("3,000.00") + "\n" + L("2,000.00", ref="4412907782", t="10:44"), "potential_split", 5000.0, 3000.0),
 C("Duplicate bank debit", 5000.0, R(), S(), L() + "\n" + L(t="10:44"), "duplicate", 5000.0, 5000.0),
 C("Failed withdrawal and reversal", 0.0, R("0.00", status="FAILED"), S(), L() + "\n" + L(dr="CR", t="14:05", d="REVERSAL"), "reversal_identified", 0.0, 5000.0),
 C("Missing bank SMS", 4940.0, R("4,940.00"), "", L(), "insufficient_evidence", 4940.0, None),
 C("Different transaction references", 4940.0, R("4,940.00"), S(ref="9900112233"), L(ref="9900112233"), "unmatched", 4940.0, 5000.0, ref="4412907781"),
]
CONCERN = {"discrepancy", "duplicate", "potential_split", "unmatched", "insufficient_evidence"}
def run(c): return A.run(c["req"], c["recv"], c["receipt"], c["sms"], c["stmt"])
def evaluate():
    rows, fx, ft, ev, evv = [], 0, 0, 0, 0
    for c in CASES:
        r = run(c); rc, sm = parse.receipt(c["receipt"]), parse.sms(c["sms"])
        got = {"cash": (rc or {}).get("cash"), "debit": (sm or {}).get("debit"), "ref": (rc or {}).get("ref")}
        for k, v in c["truth"].items(): ft += 1; fx += got[k] == v
        es = [e for f in r["findings"] for e in f["evidence"]]; ev += len(es); evv += sum(e["verified"] for e in es)
        rows.append(dict(Case=c["name"], Expected=c["expect"], Got=r["status"], Pass=r["status"] == c["expect"]))
    tp = sum(x["Expected"] in CONCERN and x["Got"] in CONCERN for x in rows); fp = sum(x["Expected"] not in CONCERN and x["Got"] in CONCERN for x in rows); fn = sum(x["Expected"] in CONCERN and x["Got"] not in CONCERN for x in rows)
    return rows, dict(status_accuracy=sum(x["Pass"] for x in rows) / len(rows), extraction_accuracy=fx / ft, evidence_verified=evv / ev if ev else 1.0,
                      precision=tp / (tp + fp) if tp + fp else 1.0, recall=tp / (tp + fn) if tp + fn else 1.0, false_accusations=fp)
