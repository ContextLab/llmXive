# Quickstart: Video Reasoning Threshold Analysis

## Prerequisites
- Python 3.10+  
- Git  
- No external data download required beyond open‑source TVQA and ConceptNet (both fetched automatically).

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

1. **Data Download** – pulls TVQA via the HuggingFace `datasets` library and ConceptNet via a verified public URL (`download_conceptnet.py`).  
2. **Annotation** – deterministic entity linking, hop counting, and covariate extraction (`annotate_graph.py`).  
3. **Linking Validation** – aborts if linking accuracy < 95 % (`annotation_coverage.json`).  
4. **Power Analysis** – computes minimum per‑bin sample size (`power_analysis.json`).  
5. **Sampling & Binning** – ensures each hop‑bin meets the required *n* ≥ 100 and creates `chain_bins.csv`.  
6. **Stratified Accuracy** – generates `accuracy_binned.png` and CSV summary.  
7. **Threshold Detection** – permutation change‑point test (covariate‑adjusted) + LRT (`threshold_results.json`).  
8. **Sensitivity Analysis** – three explicit binning schemes with covariate adjustment (`sensitivity_analysis.json`).  
9. **Predictive Model LRT** – baseline & extended logistic regressions, **confound‑adjusted LRT** (`confound_adjusted_lrt.json`), and injection of `predicted_correctness` (`model_lrt_results.json`).  
10. **Runtime & Memory Logging** – writes `runtime_log.json` and `memory_log.json`.  

All artifacts appear under `data/processed/`.

## Step‑by‑Step Execution (optional)

If you prefer to run each component individually:

```bash
# 1. Download TVQA and ConceptNet
python code/ingest/download_tvqa.py
python code/ingest/download_conceptnet.py

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

All tests must pass; failures indicate a breach of Constitution I (reproducibility) or T102/T103.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `AssertionError` in `test_entity_linker` | Embedding‑based linking (still present) | Verify `entity_linker.py` uses only exact match + Levenshtein ≤ 2 (no embeddings). |
| `RuntimeError: MemoryError` | Dataset size increased beyond CI limits | Reduce `NUM_QUESTIONS` in `download_tvqa.py` or enable streaming mode (`STREAMING=True`). |
| `Permutation test exceeds CI time` | `NUM_PERMUTATIONS` set too high | Lower `NUM_PERMUTATIONS` in `config.py` (minimum 200 for reasonable power). |
| `runtime_log.json` shows `limit_exceeded: true` | Unexpected bottleneck in a stage | Inspect `runtime_log.json` to locate the stage; consider reducing sample size or permutations. |
| `annotation_coverage.json` reports linking accuracy < 95 % | ConceptNet subgraph too sparse or entity preprocessing mismatch | Regenerate ConceptNet subset with higher entity overlap (`ENTITY_OVERLAP_RATE` in generator). |
| `threshold_results.json` missing `disconnection_rates` | Step omitted in pipeline | Ensure `detect_threshold.py` computes and writes `disconnection_rates`. |
| `confound_adjusted_lrt.json` missing | Output not generated | Verify `model_lrt.py` writes the covariate‑adjusted LRT file. |
