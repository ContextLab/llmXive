# Quickstart Guide: llmXive Follow-up (PROJ-933)

This guide describes how to run the full research pipeline end-to-end.

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`

## Execution Order

The pipeline is designed to be run sequentially. Each step produces artifacts required by the next.

### 1. Data Acquisition & Context Simulation (Phase 1)

```bash
# Download datasets (T015)
python code/data/download.py

# Preprocess and filter (T016)
python code/data/preprocess.py --mode filter

# Simulate context splits (T017)
python code/data/preprocess.py --mode split
```

**Output**: `data/context_splits.json`

### 2. Inference-Only Pass (Phase 2)

```bash
# Compute raw teacher logits (T021)
python code/models/inference_only.py --mode raw_logits
```

**Output**: `data/teacher_logits_raw.jsonl`

### 3. Teacher Distribution Averaging (Phase 2 - T048)

```bash
# Aggregate raw logits into average distribution (T048)
python code/models/inference_only.py --mode aggregate
```

**Output**: `data/teacher_distribution.json`

### 4. Training Loop (Phase 3)

```bash
# Run AntiSD training (T025)
python code/models/anti_sd_loop.py
```

**Output**: `results/training_metrics.json`, `results/memory_log.json`

### 5. Analysis & Reporting (Phase 4)

```bash
# Generate human proxy scores (T035-SIM)
python code/analysis/human_proxy_sim.py

# Compute metrics and statistical tests (T033-T037)
python code/analysis/statistical_test.py

# Final report (T038)
python code/analysis/visualize.py
```

## Full Run Command

To run the entire pipeline (excluding optional human eval recruitment which is simulated):

```bash
python code/data/download.py && \
python code/data/preprocess.py --mode all && \
python code/models/inference_only.py --mode raw_logits && \
python code/models/inference_only.py --mode aggregate && \
python code/models/anti_sd_loop.py && \
python code/analysis/human_proxy_sim.py && \
python code/analysis/statistical_test.py && \
python code/analysis/visualize.py
```

## Validation

Run the validation script to ensure all artifacts are present:

```bash
python code/data/validate_artifacts.py
```
