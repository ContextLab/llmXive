# PROJ-1071: llmXive Follow-up - Extending SynthDocBench

This project implements a decoupled retrieval pipeline to investigate and mitigate
the "middle-third" bias in Visual Language Models (VLMs) when processing long documents.

## Project Structure

- `code/`: Source code for document generation, baseline evaluation, retrieval, and analysis.
- `data/raw/`: Generated synthetic PDFs and metadata (produced by T007).
- `data/derived/`: Evaluation metrics, retrieval stats, and statistical results.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents.
- `contracts/`: Data schemas.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Ensure Tesseract OCR is installed on the system.

## Execution

Follow the task sequence in `tasks.md`:
1. T007: Generate synthetic documents.
2. T010-T013: Run baseline evaluation.
3. T014-T021: Run retrieval-augmented pipeline.
4. T022-T028: Perform statistical analysis.
