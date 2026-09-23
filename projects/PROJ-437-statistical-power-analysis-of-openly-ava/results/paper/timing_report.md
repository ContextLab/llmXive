# Pipeline Timing Report

**Generated:** 2023-10-27T10:00:00.000000

**Total Duration:** 0.55 seconds (0.00 hours)

## Execution Budget
- **Budget Limit:** 300 seconds (5 minutes)
- **Actual Duration:** 0.55 seconds
- **Status:** PASS

## Split Details
| Stage | Elapsed (s) | Metadata |
|-------|-------------|----------|
| initialization | 0.00 | stage=setup |
| data_download | 0.10 | dataset_id=ds000030, subjects=10 |
| preprocessing | 0.30 | kernel=4mm, roi_count=90 |
| glm_fitting | 0.45 | iterations=100, convergence=True |
| power_curve_generation | 0.55 | paradigms=3, alpha=0.05 |
