# MMSkills Adaptation Quickstart

This script performs a static analysis of the `skills_library` to validate the MMSkills framework structure (schema compliance, image presence, and plan consistency). It runs entirely on CPU and requires no API keys or VMs.

## Prerequisites
- Python 3.8+
- `pandas`, `matplotlib`

## Run Command
Execute the following to generate the validation report and charts:

```bash
python code/validate_mmskills.py
```

## Output Artifacts
- `data/skill_validation_report.csv`: Detailed metrics for every skill.
- `data/validation_summary.json`: Aggregate statistics (pass/fail rates).
- `figures/skill_integrity_bar.png`: Bar chart of validation statuses.
- `figures/complexity_vs_images.png`: Scatter plot of plan complexity vs image count.
