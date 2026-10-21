# Quickstart: Video Reasoning Threshold Analysis

## Prerequisites
- Python 3.10 or newer
- Git
- Access to the **VideoKR‑SFT** dataset and its knowledge graph (must be supplied manually; no public URL is verified).

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

1. **Manual placement of proprietary files**  
   Place the following files in `data/raw/` (exact filenames required):
   - `videokr_sft.jsonl` – the QA records (must contain `question_id`, `question_text`, `answer_text`, `correctness`, `difficulty_score`, answer format, etc.).  
   - `knowledge_graph.json` – the static knowledge graph used for hop counting.

   The pipeline will abort with error `E_DATA_MISSING` if either file is absent.

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

1. **Data‑availability gate** – aborts if required raw files are missing.  
2. **Annotation** – deterministic entity linking & hop counting (`annotated_videokr.csv`).  
3. **Power analysis** – determines the minimum per‑bin sample size (`power_analysis.json`).  
4. **Sampling** – ensures each hop‑bin meets the required `n`.  
5. **Stratified accuracy** – generates `accuracy_binned.png` and CSV summary.  
6. **Threshold detection** – permutation change‑point test + LRT (`threshold_results.json`).  
7. **Sensitivity analysis** – three binning schemes & covariate‑adjusted models (`sensitivity_analysis.json`).  
8. **Predictive modeling** – baseline and extended logistic regressions, LRT (`model_lrt_results.json`).  
9. **Runtime & memory logging** – writes `runtime_log.json` and `memory_log.json`.  

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
| `E_DATA_MISSING` from `download_data.py` | Required raw files not present | Place `videokr_sft.jsonl` and `knowledge_graph.json` in `data/raw/`. |
| Unit test failure in `test_entity_linker` | Incorrect fuzzy‑matching parameters | Adjust `MAX_LEVENSHTEIN_DISTANCE` in `code/utils/entity_linker.py` (default = 2). |
| Out‑of‑memory (`MemoryError`) | Dataset larger than RAM budget | Reduce `SAMPLE_SIZE` in `code/utils/config.py` or enable streaming mode (`STREAMING=True`). |
| Permutation test exceeds CI time | Too many permutations | Decrease `NUM_PERMUTATIONS` (default = 500) in `code/analysis/detect_threshold.py`. |
| Runtime exceeds 7200 s flag | Unexpected bottleneck | Inspect `runtime_log.json` for the offending stage; consider reducing sample size or permutations. |

---
