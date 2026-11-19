# PaisaProof: the Transaction Evidence Lab
Compares what a customer requested, the cash they report receiving, and what the bank recorded (receipt, SMS, statement). Fixed rules find the gap; AI only helps read messy text and word the complaint, and its numbers are checked against the verified facts. Every finding quotes its source record and shows whether the quote was found.

Run: `pip install -r requirements.txt && streamlit run app.py` (OCR for photos needs the Tesseract program; paste text works without it).

Optional Groq setup: copy `.env.example` to `.env`, add your `GROQ_API_KEY`, and restart Streamlit. Never commit `.env`; `.gitignore` excludes it. On Render, add `GROQ_API_KEY` in the service Environment settings instead. The sidebar reports whether a key is configured and whether the last actual Groq request succeeded. A configured key does not mean a request has already run; the AI fallback is only called when needed.
Tests: `pip install pytest && pytest`. The Evaluation page runs the same 8 synthetic cases live.
Deploy on Render: push to GitHub, New > Blueprint (uses `render.yaml` and the Dockerfile, which installs Tesseract), add `GROQ_API_KEY`.

Limits: demo data is synthetic; extraction is rule-based and tuned for common receipt/SMS/statement wording, so check the review step; cash received is customer reported; no complaint is ever filed automatically; this is not an official bank verification.
Credit: Streamlit, PyMuPDF, ReportLab, Tesseract/pytesseract, Groq.
