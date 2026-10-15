# Quickstart: Video Reasoning Threshold Analysis

## Prerequisites
- Python 3.10 or newer
- Git
- Access to an **open, verified** QA dataset with an associated knowledge graph (the required VideoKR‑SFT dataset is not currently available via a verified URL; you must supply a suitable substitute manually).

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

1. **Place the dataset**  
   - Put the QA CSV/JSONL file(s) and the knowledge‑graph file (e.g., `graph.json`) into `data/raw/`.  
   - The filenames must match those expected by `code/ingest/download_data.py` (e.g., `videokr_sft.csv`, `knowledge_graph.json`).  

2. **Checksum verification** (optional but recommended):
   ```bash
   python code/ingest/checksum.py
   ```

   The script will compute SHA‑256 hashes and compare them against any stored values in the project state file.

## Running the Full Pipeline

```bash
python code/main.py
```

The orchestrator performs the following steps in order:

1. **Data‑availability gate** – aborts if required files are missing.  
2. **Annotation** – deterministic entity linking & hop counting (`annotated_videokr.csv`).  
3. **Two‑stage sampling** – ensures enough high‑hop examples.  
4. **Stratified accuracy** – generates `accuracy_binned.png` and CSV summary.  
5. **Permutation change‑point test** – produces `threshold_results.json`.  
6. **Sensitivity sweep** – creates `accuracy_vs_hop_raw.png` and updates the JSON with robustness metrics.  
7. **Runtime & memory logging** – writes `runtime_log.json` and `memory_log.json`.  

All results are stored under `data/processed/`.

## Step‑by‑Step Execution (optional)

If you prefer to run each stage individually:

```bash
# 1. Annotation
python code/ingest/annotate_graph.py

# 2. Stratified accuracy
python code/analysis/stratify_accuracy.py

# 3. Threshold detection
python code/analysis/detect_threshold.py

# 4. Sensitivity analysis
python code/analysis/sensitivity.py
```

## Verification

Run the unit and integration test suites:

```bash
pytest tests/unit/
pytest tests/integration/
```

All tests must pass; otherwise the pipeline will not be considered verified (addresses T102 and T103).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `E_DATA_MISSING` error | Required raw files not present or not verified | Place the correct files in `data/raw/` and re‑run `python code/main.py`. |
| Unit test failure in `test_entity_linker` | Incorrect fuzzy‑matching parameters | Adjust `MAX_LEVENSHTEIN_DISTANCE` in `code/utils/entity_linker.py` (default = 2). |
| Out‑of‑memory (`MemoryError`) | Dataset larger than RAM budget | Reduce `SAMPLE_SIZE` in `code/utils/config.py` or enable streaming mode. |
| Permutation test takes > 6 h | Too many permutations | Decrease `NUM_PERMUTATIONS` (default = 5000) or increase parallelism (`JOBLIB_BACKEND`). |

---
