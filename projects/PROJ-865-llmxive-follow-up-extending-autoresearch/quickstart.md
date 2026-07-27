# Quickstart Guide for PROJ-865-llmxive-follow-up-extending-autoresearch

## Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`

## Execution Pipeline

The pipeline is executed in stages. Run the following commands in order.

### 1. Constitutional Gates (T002)
Validate citations in research.md before proceeding.
```bash
python code/utils/reference_validator.py
```
*If this fails, the pipeline stops immediately.*

### 2. Setup & Ingestion (T001, T009, T036)
Initialize directories and download ARC-Bench data.
```bash
python code/utils/setup_dirs.py
python code/01_data_ingestion/download_arc_bench.py
```

### 3. Annotation & Distillation (T011b, T013)
Annotate failures and distill rules.
```bash
python code/02_annotation_distillation/annotate_failures.py
python code/02_annotation_distillation/distill_rules.py
```

### 4. Execution & Comparison (T017, T019a, T021)
Run rule engine and baseline experiments.
```bash
python code/03_execution/generate_manifest.py
python code/03_execution/run_experiments.py
python code/03_execution/run_baseline.py
```

### 5. Analysis & Reporting (T025, T029f)
Perform statistical analysis and generate the final report.
```bash
python code/04_analysis/statistical_model.py
python code/04_analysis/generate_report.py
```

## Verification
Ensure all artifacts in `data/derived/` and `data/artifacts/` are generated.
Run `python code/utils/update_state.py` to finalize the project state.