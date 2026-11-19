"""Turns receipt / SMS / statement text (or OCR output) into structured records with source lines."""
import re, io, os, shutil
CUR = r"(?:rs\.?|inr|₹)\s*(\d[\d,]*(?:\.\d{1,2})?)"
REF = r"(?:ref(?:erence)?\.?\s*(?:no\.?|number|id)?|rrn|utr|txn\s*id)\s*[:#.\-]?\s*([A-Z0-9]{6,20})"
# Only treat an explicit transaction status as failure. A stray word such as
# "if not you, contact your bank" must never mark a successful debit as failed.
FAIL = r"(?:status\s*[:=]\s*(?:failed|declined|unsuccessful)|transaction\s+(?:failed|declined|unsuccessful))"
def num(s): return round(float(s.replace(",", "")), 2)
def tmin(s):
    m = re.search(r"(\d{1,2}):(\d{2})(?::\d{2})?\s*([ap]m)?", s, re.I)
    if not m: return None
    h, ap = int(m.group(1)), (m.group(3) or "").lower()
    if ap: h = h % 12 + (12 if ap == "pm" else 0)
    return h * 60 + int(m.group(2))
def find(text, label):
    for line in text.splitlines():
        m = re.search(label, line, re.I)
        if m:
            a = re.search(CUR, line[m.end():], re.I) or re.search(CUR, line, re.I)
            if a: return num(a.group(1)), line.strip()
    return None, None
def _ref(text):
    m = re.search(REF, text, re.I)
    if not m: return None, None
    return m.group(1), next(l.strip() for l in text.splitlines() if m.group(0) in l)
def receipt(text):
    if not text.strip(): return None
    cash, qc = find(text, r"cash (?:paid|dispensed|given|disbursed)|amount (?:dispensed|paid)")
    fee, qf = find(text, r"service charge|charges?|fee|commission|convenience")
    req, _ = find(text, r"requested")
    ref, qr = _ref(text)
    return dict(cash=cash, fee=fee, requested=req, ref=ref, time=tmin(text), failed=bool(re.search(FAIL, text, re.I)),
                q={"cash": qc, "fee": qf, "ref": qr}, text=text)
def sms(text):
    if not text.strip(): return None
    d, qd = find(text, r"debited|withdrawn|debit")
    fee, qf = find(text, r"service charge|charges?|fee")
    ref, qr = _ref(text)
    return dict(debit=d, fee=fee, ref=ref, time=tmin(text), failed=bool(re.search(FAIL, text, re.I)), q={"cash": qd, "ref": qr}, text=text)
def statement(text):
    rows = []
    for line in text.splitlines():
        dec = re.findall(r"\d[\d,]*\.\d{2}", line)
        if not dec: continue
        ref, _ = _ref(line)
        if not ref:
            m = re.search(r"\b(\d{9,16})\b", line); ref = m.group(1) if m else None
        rows.append(dict(amount=num(dec[0]), dir="CR" if re.search(r"\bCR\b|credit|reversal|refund", line, re.I) else "DR",
                         ref=ref, time=tmin(line), line=line.strip()))
    return rows
def to_text(name, data):
    n = name.lower()
    if n.endswith(".pdf"):
        import pymupdf
        return "\n".join(p.get_text() for p in pymupdf.open(stream=data, filetype="pdf"))
    if n.endswith((".csv", ".txt")): return data.decode("utf-8", "ignore").replace(",", " , ") if False else data.decode("utf-8", "ignore")
    try:
        import pytesseract
        from PIL import Image, ImageOps, ImageEnhance, ImageFilter
        # On Windows, pytesseract does not discover a standard Tesseract install
        # automatically. Configure the common installer path when available.
        if os.name == "nt" and not shutil.which("tesseract"):
            candidates = [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                          r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]
            for candidate in candidates:
                if os.path.isfile(candidate):
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    break
        image = Image.open(io.BytesIO(data)).convert("RGB")
        # Upscale and improve contrast for small bank-SMS screenshots.
        scale = max(1, 1800 // max(image.size))
        if scale > 1:
            image = image.resize((image.width * scale, image.height * scale))
        image = ImageOps.grayscale(image)
        image = ImageEnhance.Contrast(image).enhance(1.8).filter(ImageFilter.SHARPEN)
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text.strip()
    except Exception as exc:
        # Preserve the reason so the UI can explain an OCR failure instead of
        # silently treating an uploaded image as a missing document.
        return ""
