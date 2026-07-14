# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip
- Virtual environment (recommended)

## Setup
```bash
pip install -r requirements.txt
```

## Run the Pipeline
Execute the full analysis pipeline:
```bash
python code/main.py
```

This will:
1. Download datasets (T011)
2. Run baseline analysis (T012)
3. Record baseline metrics (T013)
4. Apply cleaning strategies (T017-T021)
5. Save cleaned datasets (T022)
6. Re-analyze cleaned variants (T023)
7. Run comparison analysis (T027)
8. Perform sensitivity analysis (T030)
9. Run bootstrap variance (T031)
10. Estimate null FPR (T032)
11. **Run outlier threshold sweep (T033)**
12. Generate forest plot (T034)
13. Generate CI heatmap (T035)
14. Generate p-value shift report (T036)
15. Generate CI width report (T037)
16. Generate effect size report (T038)
17. Log excluded datasets (T039)
18. Create comparison report (T040)
19. Generate final report (T041)

## Validate Artifacts
```bash
python code/run_quickstart_validation.py
```

## Output Files
All outputs are written to `data/processed/`:
- `baseline_metrics.json`
- `cleaned_metrics.json`
- `null_fpr_metrics.json`
- `outlier_threshold_sweep.json` (T033 output)
- `comparison_report.json`
- `final_report.txt`
- `forest_plot.png`
- `ci_heatmap.png`
