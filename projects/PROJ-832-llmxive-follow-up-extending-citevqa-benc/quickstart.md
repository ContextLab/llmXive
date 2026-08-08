# Quickstart Guide: llmXive CiteVQA Follow-up

This guide provides step-by-step instructions to set up the environment, fetch data, and run the evaluation pipeline for the CiteVQA follow-up project.

## Prerequisites

- Python 3.9+
- pip (package installer)
- A POSIX-compatible shell (bash, zsh, etc.)

## 1. Project Setup

### Create Directory Structure

Ensure the following directory structure exists in the project root:

```bash
mkdir -p code tests data/raw data/processed data/results data/logs scripts
```

### Create Required Files

Initialize Python packages and keep files:

```bash
touch code/__init__.py tests/__init__.py data/.gitkeep scripts/.gitkeep
```

### Install Dependencies

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install requirements:
 ```bash
 pip install -r requirements.txt
 ```

### Configure Linting and Formatting

The project uses `ruff` for linting and `black` for formatting. Configuration is handled via `pyproject.toml`.

Run linter:
```bash
ruff check code/
```

Run formatter:
```bash
black code/ tests/
```

## 2. Data Preparation

### Verify Data Source

The CiteVQA dataset source is verified in `data/verified_sources.json`.

### Fetch and Process Data

Run the verification script to ensure the dataset source is accessible:
```bash
python code/verify_citevqa_source.py
```

Fetch and parse the dataset:
```bash
python code/main.py --mode fetch
```
*Note: This step downloads PDFs, extracts text using `pdfplumber`, and saves processed JSONs to `data/processed/`.*

## 3. Running the Pipeline

### Text-Only Evaluation (User Story 1)

Run the full text-only retrieval and reasoning pipeline on the held-out test set:
```bash
python code/main.py --mode text_eval
```
This will:
1. Load the test set from `data/processed/`
2. Retrieve top-k text chunks using `all-MiniLM-L6-v2`
3. Generate answers using `Phi-3-mini` (4-bit quantized)
4. Save results to `data/results/text_pipeline_results.json`

### SAA Evaluation (User Story 2)

Compute Strict Attributed Accuracy (SAA) and statistical analysis:
```bash
python code/main.py --mode saa_eval
```
This will:
1. Load text pipeline results
2. Compute IoU and Semantic Similarity
3. Run one-sample t-test against the baseline
4. Generate plots in `data/results/saa_analysis.png`
5. Save summary to `data/results/saa_summary.json`

### Visual-Only Control Experiment (User Story 3)

Run the visual-only localization experiment:
```bash
python code/main.py --mode visual_eval
```
This will:
1. Load full-page images
2. Run `Phi-3-vision` (4-bit quantized)
3. Compute Visual Localization Accuracy (VLA)
4. Generate comparison report in `data/results/modality_comparison.md`

## 4. Monitoring and Logging

- **Memory Profiling**: The `main.py` script automatically profiles memory usage. Logs are saved to `data/logs/memory_profile.log`.
- **Runtime Logging**: Detailed runtime logs are written to `data/logs/execution.log`.

## 5. Verification

To ensure the pipeline runs end-to-end:
```bash
pytest tests/
```

## Troubleshooting

- **Memory Errors**: Ensure you are running in a CPU-only environment with at least 8GB RAM. The models are quantized to 4-bit to fit within limits.
- **Dataset Fetch Failures**: Check `data/verified_sources.json` and ensure network connectivity to HuggingFace.
- **Import Errors**: Verify the virtual environment is activated and `requirements.txt` is fully installed.
