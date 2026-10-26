# Quickstart: MobileForge Logic Distillation

## Prerequisites
- Python 3.11+  
- Git  
- Linux environment (local VM or GitHub Actions runner)  
- Internet access (only to fetch required Python packages and the verified ExtractionDataset parquet)  

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-930-llmxive-follow-up-extending-mobileforge

# Install exact dependencies
pip install -r code/requirements.txt
```

### Environment Variables
Create a `.env` file or export manually:

```bash
export RANDOM_SEED=42
# If an open MobileForge log source becomes available, set:
# export MOBILEFORGE_LOGS_URL="https://example.com/mobileforge/logs.zip"
```

## Execution Workflow

### Step 0: Bootstrap & Directory Creation
```bash
python code/bootstrap.py
# Verifies that all required directories (including code/models/, code/data/raw/, etc.) exist.
```

### Step 1: Data Download & Validation (FR‑001)
```bash
# This will abort with a clear error if MOBILEFORGE_LOGS_URL is not set.
python code/pipeline/download_mobileforge.py

# Validate that all hints are purely linguistic.
python code/data/raw/validate_extraction_dataset.py
# On success you will see "Validation passed: flagged hints were negligible."
```

> **Important**: At present there is **no publicly available MobileForge log dataset**. The pipeline will stop here until such data are provided. The script is intentionally a placeholder – it does **not** fabricate data.

### Step 2: Use Verified ExtractionDataset (Optional Demonstration)
If you wish to run the pipeline with the open ExtractionDataset as a stand‑in:

```bash
python code/pipeline/extract.py \
  --source https://huggingface.co/datasets/OSTShushack/ExtractionDataset/resolve/main/data/test-00000-of-00001.parquet \
  --output-dir outputs/
```

This will produce `train_split.parquet`, `test_split.parquet`, and `extraction_meta.json`.

### Step 3: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py
# Writes outputs/power_analysis.json
```

### Step 4: Model Training (FR‑002, SC‑003)
```bash
# Quick sanity check (optional)
python code/pipeline/train.py --pilot

# Full training (will abort if >6 h or if CUDA is detected)
python code/pipeline/train.py
# Model checkpoint saved to code/models/distilled_distilbert/
```

### Step 5: Evaluation & Paired McNemar’s Test (FR‑003‑005)
```bash
python code/pipeline/evaluate.py
# Generates outputs/evaluation_results.json
```

### Step 6: Sensitivity Sweep (FR‑006)
*Performed automatically inside `evaluate.py`; results are embedded in `outputs/evaluation_results.json`.*

### Step 7: Hint‑Specific Ablation (Constitution VII)
```bash
python code/pipeline/evaluate.py --mode ablation
# Ablation results are merged into the same evaluation_results.json.
```

### Step 8: Verification
```bash
pytest tests/
# Runs unit, integration, and contract tests.
```

## Troubleshooting
- **Missing MobileForge logs**: The pipeline halts at Step 1 with a clear message. Provide a valid `MOBILEFORGE_LOGS_URL` or wait for a spec revision.  
- **Training exceeds 6 h**: Watchdog will kill the process; reduce `--max-epochs` or the training subset size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run the download step; the script will re‑download corrupted files.  

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-930-llmxive-follow-up-extending-mobileforge/specs/001-llmxive-follow-up-extending-mobileforge/contracts/dataset.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "ExtractionDataset"
description: "Schema for the raw and processed triples dataset."
type: "object"
properties:
  triples:
    type: "array"
    items:
      type: "object"
      properties:
        ui_state:
          type: "string"
          description: "JSON string or caption representing the UI state."
        corrective_hint:
          type: "string"
          description: "Linguistic instruction without coordinates."
        action:
          type: "string"
          description: "Ground truth action sequence."
        trajectory_status:
          type: "string"
          enum:
            - "failed_then_success"
            - "success"
            - "none"
            - "initial_success"
          description: "Status of the trajectory."
      required:
        - ui_state
        - corrective_hint
        - action
        - trajectory_status
  metadata:
    type: "object"
    properties:
      source_log:
        type: "string"
        description: "Source log file name."
      filtering_criteria:
        type: "string"
        description: "Criteria used to filter the data."
    # metadata is optional; absence does not cause validation failure
required:
  - triples
additionalProperties: false