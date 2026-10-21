# Quickstart: Video Reasoning Threshold Analysis

## Prerequisites
- Python 3.10 or newer
- Git
- Access to an **open‑access video‑question‑answer dataset** (TVQA) that can serve as a functional substitute for the proprietary VideoKR‑SFT data.

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

## Data Setup

1. **Automatic download of TVQA**  
   The pipeline will fetch the TVQA dataset from HuggingFace (`datasets.load_dataset("tvqa")`). No manual placement is required.  
   If you wish to use a different open dataset, adjust `code/ingest/download_data.py` accordingly.

2. **Optional checksum verification** (recommended)

   ```bash
   python code/ingest/checksum.py
   ```

   This computes SHA‑256 hashes of the raw files and records them in the project state file for reproducibility (Constitution III).

## Running the Full Pipeline

```bash
python code/main.py
```

The orchestrator performs the following ordered steps:

1. **Data‑availability gate** – verifies that the TVQA files are present (downloaded automatically).  
2. **Annotation** – deterministic entity linking & hop counting (`annotated_videokr.csv`).  
3. **Linking Validation** – computes linking accuracy on a curated validation set; aborts if < 95 %.  
4. **Power analysis** – determines the minimum per‑bin sample size (`power_analysis.json`).  
5. **Sampling** – ensures each hop‑bin meets the required `n`.  
6. **Stratified accuracy** – generates `accuracy_binned.png` and CSV summary.  
7. **Threshold detection** – permutation change‑point test + LRT (`threshold_results.json`).  
8. **Sensitivity analysis** – three binning schemes & covariate‑adjusted models (`sensitivity_analysis.json`).  
9. **Predictive modeling** – baseline and extended logistic regressions, LRT (`model_lrt_results.json`) **and writes** `predicted_correctness` back into `annotated_videokr.csv`.  
10. **Runtime & memory logging** – writes `runtime_log.json` and `memory_log.json`.  

All results are stored under `data/processed/`.

## Step‑by‑Step Execution (optional)

If you prefer to run each stage individually:

```bash
# 1. Annotation
python code/ingest/annotate_graph.py

# 2. Power analysis
python code/analysis/power_analysis.py

# 3. Stratified accuracy
python code/analysis/stratify_accuracy.py

# 4. Threshold detection
python code/analysis/detect_threshold.py

# 5. Sensitivity analysis
python code/analysis/sensitivity.py

# 6. Predictive model LRT
python code/analysis/model_lrt.py
```

## Verification

Run the unit and integration test suites:

```bash
pytest tests/unit/
pytest tests/integration/
```

All tests must pass; otherwise the pipeline is considered invalid (addresses Constitution I & T102/T103).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `E_DATA_MISSING` from `download_data.py` | TVQA files not downloaded | Re‑run `python code/ingest/download_data.py` or check internet connectivity. |
| Unit test failure in `test_entity_linker` | Embedding‑based path still active | Ensure `entity_linker.py` uses only exact match + Levenshtein (embedding branch removed). |
| Out‑of‑memory (`MemoryError`) | Dataset larger than RAM budget | Reduce `SAMPLE_SIZE` in `code/utils/config.py` or enable streaming mode (`STREAMING=True`). |
| Permutation test exceeds CI time | Too many permutations | Decrease `NUM_PERMUTATIONS` (default = 500) in `code/analysis/detect_threshold.py`. |
| Runtime exceeds 7200 s flag | Unexpected bottleneck | Inspect `runtime_log.json` for the offending stage; consider reducing sample size or permutations. |

---


