# Quickstart: Video Reasoning Threshold Analysis

## Prerequisites

- Python 3.10+  
- Git  
- No external data download required beyond the official VideoKR‑SFT release (downloaded automatically).

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-961-llmxive-follow-up-extending-videokr-towa

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/main.py
```

The orchestrator executes the following ordered steps:

1. **Data Download** – pulls the official **VideoKR‑SFT** dataset and its **ground‑truth knowledge graph** via `code/ingest/download_videokr.py` and `code/ingest/download_kg.py`. If either download fails or the files are missing, the pipeline aborts with a clear error message (no TVQA or ConceptNet fallback).  
2. **Annotation** – deterministic entity linking, hop counting, and covariate extraction (`annotate_graph.py`).  
3. **Linking Validation** – aborts if linking accuracy < 95 % (`annotation_coverage.json`).  
4. **Power Analysis** – computes minimum per‑bin sample size (`power_analysis.json`).  
5. **Sampling & Binning** – ensures each hop‑bin meets *n* ≥ 100 and creates `chain_bins.csv`.  
6. **Stratified Accuracy** – generates `accuracy_binned.png` and CSV summary.  
7. **Threshold Detection** – permutation change‑point test (10,000 permutations) + LRT (`threshold_results.json`).  
8. **Sensitivity Analysis** – three explicit binning schemes with covariate adjustment (`sensitivity_analysis.json`).  
9. **Predictive Model LRT** – baseline & extended logistic regressions, covariate‑adjusted LRT (`confound_adjusted_lrt.json`), and injection of `predicted_correctness` (`model_lrt_results.json`).  
10. **Runtime & Memory Logging** – writes `runtime_log.json` and `memory_log.json`.  

All artifacts appear under `data/processed/`.

## Step‑by‑Step Execution (optional)

```bash
# 1. Download VideoKR‑SFT and its KG
python code/ingest/download_videokr.py
python code/ingest/download_kg.py

# 2. Annotation
python code/ingest/annotate_graph.py

# 3. Power analysis
python code/analysis/power_analysis.py

# 4. Stratified accuracy
python code/analysis/stratify_accuracy.py

# 5. Threshold detection
python code/analysis/detect_threshold.py

# 6. Sensitivity analysis
python code/analysis/sensitivity.py

# 7. Predictive model LRT
python code/analysis/model_lrt.py
```

## Verification

Run the test suites to ensure reproducibility:

```bash
pytest tests/unit/
pytest tests/integration/
```

All tests must pass; failures indicate a breach of Constitution I (reproducibility) or other constraints.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `FileNotFoundError` for VideoKR‑SFT files | Dataset not downloaded or corrupted | Re‑run `download_videokr.py`; check `dataset_verification.json`. |
| `AssertionError` in `test_entity_linker` | Linking accuracy below 95 % | Review `entity_linker.py` logs; improve exact‑match coverage or adjust fuzzy threshold. |
| `RuntimeError: MemoryError` | Dataset size exceeds CI limits | Enable streaming mode in `download_videokr.py` or process a smaller random seed sample. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS` set too high | Verify `config.py` sets `NUM_PERMUTATIONS = 10000`; reduce only if CI runtime limit is breached (adjust with caution). |
| `runtime_log.json` shows `limit_exceeded: true` | Unexpected bottleneck | Inspect `runtime_log.json` to locate stage; consider reducing sample size or permutations. |
| `annotation_coverage.json` reports linking accuracy < 95 % | KG mismatch or poor entity coverage | Regenerate KG subset limited to entities present in VideoKR‑SFT; re‑run annotation. |
| `threshold_results.json` missing `disconnection_rates` | Step omitted | Ensure `detect_threshold.py` computes and writes them. |
| `confound_adjusted_lrt.json` missing | Output not generated | Verify `model_lrt.py` writes the file after covariate‑adjusted analysis. |
