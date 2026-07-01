# Quickstart: Emotional Contagion Analysis

## Prerequisites

- Python 3.11+
- Git
- 7 GB+ RAM (for full dataset processing)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-139-the-influence-of-emotional-contagion-on-/
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

3. **Download NLTK Data**:
   The sentiment analysis script requires VADER lexicons.
   ```bash
   python -c "import nltk; nltk.download('vader_lexicon')"
   ```

## Data Acquisition

The pipeline uses verified HuggingFace datasets. Do not manually download files; use the provided script to ensure checksums are recorded.

```bash
# Run the download script (fetches from verified URLs)
python code/data/download.py --source askScience --source fdr
```

*Output*: `data/raw/askScience.jsonl`, `data/raw/fdr.parquet`.

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/analysis/run_pipeline.py
```

This script performs:
1. **Extraction**: Identifies threads with ≥3 seed posts.
2. **Sentiment**: Computes VADER scores and Contagion Index.
3. **Metrics**: Calculates decision quality and ground truth validation.
4. **Modeling**: Fits GLMMs and applies FDR correction.
5. **Sensitivity**: Sweeps thresholds as per FR-008.

## Verification

1. **Check Outputs**:
   ```bash
   ls data/processed/
   # Expected: thread_metrics.csv, model_results.json, sensitivity_report.csv
   ```

2. **Run Tests**:
   ```bash
   pytest code/tests/ -v
   ```

3. **Reproducibility Check**:
   Re-run the pipeline. Verify that `data/processed/` files have identical checksums (recorded in `state/`).

## Troubleshooting

- **Memory Error**: If RAM > 7 GB, the script automatically samples threads. Check logs for `SAMPLED` warnings.
- **GLMM Convergence**: If models fail, the script falls back to Fixed Effects with Robust SEs. Check `modeling.log`.
- **Ground Truth Missing**: If <30% of threads have ground truth, the `external_validation_score` column will be mostly `null`. This is expected behavior per FR-009.
