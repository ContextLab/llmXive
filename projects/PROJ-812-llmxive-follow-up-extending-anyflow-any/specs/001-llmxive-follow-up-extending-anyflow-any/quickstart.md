# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Prerequisites
- Python 3.11+
- Git
- Internet access (to download HF datasets)
- 2 CPU cores, ≤ 7 GB RAM (GitHub Actions free tier)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-812-llmxive-follow-up-extending-anyflow-any
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Annotation Step (Human‑Generated Ground Truth)

1. **External Annotation**: Use a tool like Label Studio or Google Forms to collect scores from **two** independent annotators for the curated clips. Export the results as a CSV.
2. **Ingest Annotations**: Run the ingestion script to load the external CSV:

   ```bash
   python code/annotation/collect_annotations.py --input-csv external_annotations.csv --clip-dir data/raw/video_clips/
   ```

3. **Validate & Adjudicate**: Validate inter‑annotator agreement and resolve disagreements:

   ```bash
   python code/annotation/validate_annotations.py data/raw/ground_truth.csv
   python code/annotation/adjudicate.py data/raw/ground_truth.csv
   ```

   - If Cohen’s κ < 0.81 the pipeline aborts.
   - Disagreements are automatically forwarded to `annotation/adjudicate.py` for a third expert.

   The resulting immutable CSV `data/raw/ground_truth.csv` is checksummed before any further processing.

## Running the Full Pipeline

The orchestrator enforces strict phase ordering:

```bash
python code/main.py
```

This will:

1. Verify all external URLs (`utils/reference_validator.py`).  
2. Download & stratify a representative set of video clips (`download_and_stratify.py`).  
3. Generate `data/checksums.json`.  
4. Load the AnyFlow ONNX model (`load_onnx.py`).  
5. Compute divergence metrics (`compute_divergence.py`).  
6. Perform control analysis, Fisher r‑to‑z test, correlation/IPW, logistic regression, and sensitivity sweeps.  
7. Run the synthetic‑subset validation (`synthetic_validation_subset.py`).  
8. Produce `results/final_report.md` and all CSV/JSON artifacts.

## Expected Outputs
- `data/processed/divergence_scores.csv`  
- `data/processed/sensitivity_report.csv`  
- `data/processed/variance_report.csv`  
- `data/processed/control_analysis.json`  
- `results/final_report.md` (includes explicit associational framing)

## Runtime & Resources
- **Estimated wall‑time**: 4–5 h on the free‑tier runner (≤ 6 h budget).  
- **Peak RAM**: < 7 GB (streaming).  
- **GPU**: Not required; all code runs on CPU.  

## Verification
```bash
pytest tests/
```
All tests include contract validation (`test_contracts.py`) against the YAML schemas in `contracts/`.