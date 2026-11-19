import pytest
from paisaproof import samples
@pytest.mark.parametrize("c", samples.CASES, ids=lambda c: c["name"])
def test_case(c): assert samples.run(c)["status"] == c["expect"]


def test_sms_parser_accepts_bank_debit_alert():
    from paisaproof import parse
    text = "SAHARA DEMO BANK\n18-Nov-2026 10:43 AM\n\nRs 5,000.00 debited from A/c XX4821\non 18-11-2026 10:43 for CSP WDL\nRef 4412907781. If not you, contact\nyour bank."
    sm = parse.sms(text)
    assert sm is not None
    assert sm["debit"] == 5000.00
    assert sm["ref"] == "4412907781"
    assert sm["failed"] is False


def test_explicit_failed_receipt_is_detected():
    from paisaproof import parse
    assert parse.receipt("Cash paid Rs 4,940.00\nRef 4412907781\nStatus: FAILED")["failed"] is True


def test_unrelated_failure_word_does_not_mark_receipt_failed():
    from paisaproof import parse
    assert parse.receipt("Cash paid Rs 5,000.00\nRef 4412907781\nIf transaction not received, contact support")["failed"] is False
