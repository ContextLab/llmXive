# Quickstart Validation Guide

## Purpose

This document describes how to validate the end-to-end reproducibility of the
`PROJ-294-evaluating-the-impact-of-code-generation` research pipeline.

## Prerequisites

- Python 3.8+
- All dependencies installed from `code/requirements.txt`
- Git repository with all source files

## Validation Steps

### 1. Verify Directory Structure

The following directories must exist:

```bash
data/
├── raw/ # Downloaded datasets (HumanEval)
├── generated/ # Intermediate generated code
└── analysis/ # Metrics and statistical results

results/
└── figures/ # Generated plots and charts

state/
└── artifact_hashes.yaml # Integrity tracking
```

### 2. Verify Core Scripts

All pipeline scripts must be present in `code/`:

- `download_data.py` - Downloads HumanEval dataset
- `generate_code.py` - Generates code using LLM models
- `analyze_metrics.py` - Computes complexity and coverage metrics
- `statistical_tests.py` - Performs hypothesis testing
- `report_generator.py` - Creates final Markdown report
- `utils.py` - Shared utilities (logging, hashing)

### 3. Run Validation Script

Execute the automated validation script:

```bash
cd code
python validate_quickstart.py
```

This script will:

1. Check directory structure
2. Verify dataset integrity (HumanEval)
3. Validate metrics.json structure and sample count (≥40)
4. Check statistical results
5. Verify report and figures existence
6. Confirm state file integrity

### 4. Expected Artifacts

After a successful run, the following artifacts must exist:

| Artifact | Path | Description |
|----------|------|-------------|
| HumanEval | `data/raw/humaneval.json` | Original dataset |
| Metrics | `data/analysis/metrics.json` | Computed metrics for all samples |
| Statistics | `data/analysis/statistical_results.json` | Test results |
| Report | `results/results_report.md` | Final Markdown report |
| Figures | `results/figures/*.png` | Plots and charts |
| State | `state/artifact_hashes.yaml` | Integrity checksums |

### 5. Manual Verification

If the automated script fails, manually verify:

```bash
# Check metrics.json structure
python -c "
import json
with open('data/analysis/metrics.json') as f:
 data = json.load(f)
assert len(data) >= 40, 'Insufficient samples'
required = ['task_id', 'cyclomatic_complexity', 'halstead_volume', 'branch_coverage_pct', 'pass_rate']
assert all(k in data[0] for k in required), 'Missing keys'
print('Metrics validation passed')
"

# Check report content
grep -q "Cyclomatic Complexity" results/results_report.md && echo "Report contains expected sections"
```

## Troubleshooting

### Missing HumanEval Data

If `data/raw/humaneval.json` is missing:

```bash
python code/download_data.py
```

### Missing Metrics

If `data/analysis/metrics.json` is missing:

```bash
python code/generate_code.py
python code/analyze_metrics.py
```

### Missing Report

If `results/results_report.md` is missing:

```bash
python code/report_generator.py
```

## Success Criteria

- [x] All directories exist
- [x] HumanEval dataset downloaded and verified
- [x] `metrics.json` contains ≥40 samples with all required fields
- [x] Statistical results file exists with valid structure
- [x] Final report contains all required sections
- [x] At least 3 figures generated in `results/figures/`
- [x] State file tracks artifact hashes

## Integration with CI/CD

Add to CI pipeline:

```yaml
validate:
 script:
 - cd code
 - python validate_quickstart.py
 artifacts:
 paths:
 - data/
 - results/
 - state/
```

## References

- Task T039: Run quickstart.md validation
- FR-001: Data integrity verification
- FR-006: Automated report generation
- Plan: Reproducibility Requirements
