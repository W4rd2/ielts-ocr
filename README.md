# IELTS Scanner

Streamlit app that extracts IELTS certificate data via OCR, validates fields, and exports tidy Excel workbooks.

## Why this structure
- `app.py` — single entrypoint (`streamlit run app.py`).
- `src/ielts_scanner/config.py` — shared constants and environment guards.
- `src/ielts_scanner/core/` — low-level helpers (parsing, grading).
- `src/ielts_scanner/models/` — data classes (e.g., `ExamResult`).
- `src/ielts_scanner/features/` — feature slices:
  - `ocr.py` — EasyOCR-driven text extraction and scoring rules.
  - `pdf_ingest.py` — PDF/page splitting and image materialization.
  - `excel_export.py` — dedup + Excel writer.
  - `session_management.py` — Streamlit session + temp folder lifecycle.
  - `ui.py` — Streamlit layout and user flow.

## Prerequisites
- Python 3.11+ recommended.
- System deps:
  - Poppler (for `pdf2image`): ensure `pdftoppm/pdftocairo` are on PATH.
  - Tesseract **not** required (EasyOCR ships its own models).
- GPU: EasyOCR will use CUDA/MPS if available; falls back to CPU.

## Setup
```bash
python -m venv .venv
. .venv/Scripts/activate           # Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Running
```bash
streamlit run app.py
```
The app will create `IELTS-Scanner_data_folder` for sessions, outputs, and model cache.

## Validation
```bash
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m compileall -q src app.py
```

## Usage notes
- Upload PNG/JPG/PDF certificates in the UI; PDFs are split into single pages automatically.
- Excel output is offered when processing completes; rejected/faulty rows go to dedicated sheets.
- “First Day of Classes” is stored in `IELTS-Scanner_data_folder/data.txt` to expire certificates older than two years.

## Project layout
```
app.py
requirements.txt
src/
  ielts_scanner/
    config.py
    core/
      grades.py
      utils.py
    models/
      exam_result.py
    features/
      ocr.py
      pdf_ingest.py
      excel_export.py
      session_management.py
      io_utils.py
      ui.py
```

## Deployment tips
- For Streamlit Cloud or container use, pin package versions to avoid OCR model drift.
- Mount `IELTS-Scanner_data_folder` to persistent storage if you need to retain outputs between restarts.
- On Windows, ensure Poppler binaries are available on PATH before containerizing or scheduling.

## Troubleshooting
- **Poppler missing**: `pdf2image.exceptions.PDFInfoNotInstalledError`; install Poppler and retry.
- **GPU memory errors**: set `CUDA_VISIBLE_DEVICES=` to force CPU or adjust GPU drivers.
- **Blank/garbled OCR**: check image contrast; `ocr.apply_filters` auto-enhances but may need higher DPI inputs.
