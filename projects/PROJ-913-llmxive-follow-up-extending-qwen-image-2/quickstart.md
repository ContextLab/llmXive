# Quickstart Guide

## Prerequisites
- Python 3.9+
- Access to Hugging Face Hub (token required in `HF_TOKEN` env var)

## Installation
1. Navigate to the project root: `cd projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2`
2. Install dependencies: `pip install -r code/requirements.txt`

## Execution Pipeline
Run the tasks in the following order:

### Phase 1: Setup & Foundation
```bash
# Ensure directory structure exists
python code/utils/setup_data_dirs.py
```

### Phase 2: Data Acquisition (US1)
```bash
# Download models
python code/data/download_models.py
python code/data/download_vlms.py
python code/data/download_proxy.py

# Verify integrity
python code/data/verify_checksums.py

# Curate Pilot Prompts
python code/data/curate_id_prompts.py
python code/data/curate_ood_prompts.py

# Validate OOD (Critical Gate)
python code/data/validate_ood.py
python code/utils/pipeline_gate.py
```

### Phase 3: Pilot Inference (US2)
```bash
python code/inference/generate_pilot.py
```

### Phase 4: Power Analysis
```bash
python code/analysis/power_analysis.py
```

### Phase 5: Full Inference & Analysis (If Gate Passes)
```bash
python code/data/curate_full.py
python code/inference/generate_full.py
python code/analysis/scoring.py
python code/analysis/compute_degradation.py
python code/analysis/calculate_gap.py
python code/analysis/statistical_test.py
python code/analysis/external_consistency.py
python code/analysis/report.py
```

## Notes
- All inference runs on CPU by default (float16).
- OOD validation must pass before any generation occurs.
- Check `data/logs/` for execution logs.
