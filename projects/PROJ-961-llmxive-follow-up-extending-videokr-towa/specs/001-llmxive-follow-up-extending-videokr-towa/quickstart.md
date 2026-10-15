# Quickstart: Video Reasoning Threshold Analysis

## Prerequisites
- Python 3.10 or newer
- Git
- Access to the **VideoKR‑SFT** dataset and its knowledge graph (no public URL is verified; you must provide the files manually **or** let the pipeline download the open substitute).

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

1. **Place the raw data** *(if you have the proprietary files)*  
   - Copy the QA file (e.g., `videokr_sft.jsonl`) and the knowledge‑graph file (`knowledge_graph.json`) into `data/raw/`.  
   - Filenames must match those expected by `code/ingest/download_data.py`.  

2. **Automatic open‑source fallback**  
   If the proprietary files are absent, the pipeline will automatically download the open‑source `video_qa_sample` dataset from HuggingFace:

   ```bash
   python -c "from datasets import load_dataset; load_dataset('video_qa_sample')"
   ```

   The download will be cached under `~/.cache/huggingface/datasets/` and used as a surrogate for the analysis.

3. **Optional checksum verification**  
   ```bash
   python code/ingest/checksum.py
   ```
   This will compute SHA‑256 hashes and compare them to any stored values in the project state file.

## Running the Full Pipeline

```bash
python code/main.py
```

The orchestrator performs the following steps in order:

1. **Data‑availability gate** – aborts if required raw files are missing **and** the open substitute cannot be fetched (addresses T103).  
2. **Annotation** – deterministic entity linking & hop counting (`annotated_videokr.csv`).  
3. **Power analysis** – determines the minimum per‑bin sample size (`power_analysis.json`).  
4. **Two‑stage sampling** – ensures each hop‑bin meets the required `n`.  
5. **Stratified accuracy** – generates `accuracy_binned.png` and CSV summary.  
6. **Threshold detection** – permutation change‑point test + LRT (`threshold_results.json`).  
7. **Sensitivity analysis** – runs three binning schemes and covariate‑adjusted models (`sensitivity_analysis.json`).  
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

All tests must pass; otherwise the pipeline is considered invalid (addresses T102 and T103).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `E_DATA_MISSING` error from `download_data.py` | Required raw files not present and open substitute failed to download | Ensure internet access; the script will attempt to fetch `video_qa_sample` from HuggingFace. |
| Unit test failure in `test_entity_linker` | Incorrect fuzzy‑matching parameters | Adjust `MAX_LEVENSHTEIN_DISTANCE` in `code/utils/entity_linker.py` (default = 2). |
| Out‑of‑memory (`MemoryError`) | Dataset larger than RAM budget | Reduce `SAMPLE_SIZE` in `code/utils/config.py` or enable streaming mode (`STREAMING=True`). |
| Permutation test exceeds CI time | Too many permutations | Decrease `NUM_PERMUTATIONS` (default = 500) in `code/analysis/detect_threshold.py`. |
| Runtime exceeds 7200 s flag | Unexpected bottleneck | Check `runtime_log.json` for the offending stage and consider reducing sample size or permutations. |

---


