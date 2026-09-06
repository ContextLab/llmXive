# Quickstart Guide: llmXive Follow-up

## Prerequisites

- Python 3.11+
- Tesseract OCR (system package)
- `pip`

## Setup

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Install Tesseract OCR:
 - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
 - macOS: `brew install tesseract`
 - Windows: Download installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

## Running the Pipeline

Follow the task sequence in `tasks.md`:

1. **Generate Data**: Run `python code/doc_generator.py` (Task T007).
2. **Baseline Evaluation**: Run `python code/baseline_eval.py` (Tasks T010-T012).
3. **Retrieval Pipeline**: Run `python code/retrieval_index.py` then `python code/retrieval_eval.py` (Tasks T014-T019).
4. **Statistical Analysis**: Run `python code/stats_analysis.py` (Tasks T022-T027).

## Output Artifacts

- `data/raw/`: Synthetic PDFs and metadata.
- `data/derived/baseline_metrics.json`: Baseline accuracy and bias metrics.
- `data/derived/retrieval_metrics.json`: Retrieval precision/recall and VLM accuracy with retrieval.
- `data/derived/statistical_results.json`: Correlation analysis results.
