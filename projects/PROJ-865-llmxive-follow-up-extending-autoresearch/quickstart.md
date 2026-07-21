# llmXive Follow-up: AutoResearchClaw Pipeline Quickstart

This document provides instructions for running the complete AutoResearchClaw pipeline, including data ingestion, rule distillation, execution, and statistical analysis. It also covers running the external baseline comparison.

## Prerequisites

- Python 3.9+
- Required dependencies installed: `pip install -r requirements.txt`
- HuggingFace CLI installed (for ARC-Bench dataset)
- Sufficient disk space (~5GB for datasets and artifacts)

## Project Structure

```
.
├── code/
│ ├── 01_data_ingestion/
│ ├── 02_annotation_distillation/
│ ├── 03_execution/
│ ├── 04_analysis/
│ ├── utils/
│ └── tests/
├── data/
│ ├── raw/
│ ├── derived/
│ └── artifacts/
├── specs/
│ └── 001-llmxive-followup/
├── state/
└── requirements.txt
```

## Step-by-Step Pipeline Execution

### 1. Initialize Project Structure (One-time setup)

```bash
python code/setup/init_project_structure.py
```

This creates all required directories and `.gitkeep` files.

### 2. Download ARC-Bench Dataset

```bash
python code/data_ingestion/download_arc_bench.py
```

**Output**: `data/raw/arc_bench_25_topic_subset.json`

### 3. Parse Reasoning Traces

```bash
python code/01_data_ingestion/parse_reasoning_traces.py
```

**Output**: `data/derived/parsed_traces.json`

### 4. Annotate Failure Cases

```bash
python code/02_annotation_distillation/annotate_failures.py
```

**Outputs**:
- `data/derived/failure_cases.json` (annotated dataset)
- Validates against `specs/001-llmxive-followup/contracts/failure_case.schema.yaml`

### 5. Distill Rules Library

```bash
python code/02_annotation_distillation/distill_rules.py
```

**Outputs**:
- `data/derived/rules_library.json` (distilled rules)
- `data/derived/fallback_status.json` (if regex fallback triggered)
- Validates against `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`

**Note**: This step includes automatic retry logic and RAM monitoring. If RAM exceeds 6GB, it switches to regex-based extraction.

### 6. Generate Experiment Manifest

```bash
python code/03_execution/generate_manifest.py
```

**Output**: `data/derived/experiment_manifest.csv` (100 stratified task IDs)

### 7. Run Rule Engine Experiments

```bash
python code/03_execution/run_experiments.py
```

**Outputs**:
- `data/derived/rule_engine_results.json`
- `data/derived/results.csv` (partial, before baseline merge)

### 8. Run External Baseline Comparison

The baseline agent runs on external resources. This script orchestrates the process and waits for results.

```bash
python code/03_execution/run_baseline_external.py
```

**Outputs**:
- `data/derived/baseline_results.json` (from external runner)
- The script waits for the external baseline to complete (with timeout)

**Manual External Execution** (if not automated):
```bash
python code/03_execution/run_baseline.py --manifest data/derived/experiment_manifest.csv --output data/derived/baseline_results.json
```

### 9. Merge Results

```bash
python code/03_execution/run_experiments.py
```

**Note**: Running `run_experiments.py` again will merge the rule engine results with the baseline results from `data/derived/baseline_results.json`.

**Output**: `data/derived/results.csv` (complete, with both methods)

### 10. Statistical Analysis

Run all analysis scripts in order:

```bash
# Mixed-effects regression
python code/04_analysis/statistical_model.py

# Time-to-pivot difference test
python code/04_analysis/time_diff_test.py

# Error taxonomy
python code/04_analysis/error_taxonomy.py

# Stratified success rates
python code/04_analysis/calculate_stratified_rates.py

# Final report generation
python code/04_analysis/generate_final_report.py
```

**Outputs**:
- `data/derived/regression_results.json`
- `data/derived/time_diff_results.json`
- `data/derived/error_taxonomy_results.json`
- `data/derived/stratified_success_rates.csv`
- `data/derived/final_report.md`

### 11. Update State File

```bash
python code/utils/update_state.py
```

**Output**: `state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` (updated with artifact hashes)

### 12. Compliance Audit

```bash
python code/02_annotation_distillation/log_compliance_audit.py
```

**Output**: `data/derived/compliance_audit_log.json`

## Running Tests

```bash
# Unit tests
python -m pytest code/tests/test_annotation.py -v

# Integration tests
python -m pytest code/tests/test_pipeline.py -v

# Rule engine tests
python -m pytest code/tests/test_rule_engine.py -v
```

## Linting and Formatting

```bash
# Check linting
python code/utils/lint_format_config.py --check-lint

# Check formatting
python code/utils/lint_format_config.py --check-format

# Apply fixes
python code/utils/lint_format_config.py --apply
```

## Troubleshooting

### Memory Issues
If you encounter memory errors during rule distillation:
- The script automatically switches to regex-based extraction if RAM > 6GB
- Check `data/derived/fallback_status.json` for fallback details

### Missing Baseline Results
If `data/derived/baseline_results.json` is missing:
- Manually run the external baseline: `python code/03_execution/run_baseline.py --manifest data/derived/experiment_manifest.csv --output data/derived/baseline_results.json`
- Ensure the manifest file exists and contains valid task IDs

### Schema Validation Errors
If validation fails:
- Check `specs/001-llmxive-followup/contracts/` for the required schema files
- Ensure all output files match their corresponding schemas

## Resource Limits

The pipeline enforces the following resource limits (configurable in `code/utils/config.py`):
- MAX_CPU_CORES: 2
- MAX_MEMORY_GB: 7

A resource watchdog monitors usage and will terminate the process if limits are exceeded.

## Expected Artifacts

After a successful run, you should have:

| File | Description |
|------|-------------|
| `data/derived/failure_cases.json` | Annotated failure cases |
| `data/derived/rules_library.json` | Distilled rule library |
| `data/derived/experiment_manifest.csv` | 100 stratified task IDs |
| `data/derived/results.csv` | Merged results (rule engine + baseline) |
| `data/derived/regression_results.json` | Statistical analysis results |
| `data/derived/final_report.md` | Comprehensive final report |
| `state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` | Project state with artifact hashes |