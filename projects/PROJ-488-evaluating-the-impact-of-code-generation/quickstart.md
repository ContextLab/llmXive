# Quick Start Guide

## Prerequisites

Before running this pipeline, ensure the following Constitutional Amendment PRs are **merged** and approved:

- **Amendment VI**: Permitting CodeParrot/CodeGen datasets (see `docs/amendment-vi.md`).
- **Amendment VII**: Permitting radon/pylint static analysis (see `docs/amendment-vii.md`).

The pipeline will check the state file `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` for `amendment_status`. If either amendment is not marked as `approved`, the run will abort with **Error 101**.

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (Python 3.11 recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## One-Command Execution

To run the entire pipeline from data ingestion to statistical analysis and guideline generation, execute:

```bash
python code/main.py --run-all
```

This command performs the following steps in order:
1. **Amendment Check**: Verifies that Amendment VI and VII are approved in the state file.
2. **Data Ingestion**: Downloads CodeSearchNet and CodeParrot/CodeGen datasets, filters to Python functions, and balances lengths.
3. **Metric Extraction**: Computes radon complexity and pylint bug indicators.
4. **Statistical Analysis**: Performs Mann-Whitney U tests, Cliff's delta, and Benjamini-Hochberg correction.
5. **Visualization**: Generates boxplots for all metrics.
6. **Guideline Generation**: Produces review recommendations based on significant results.
7. **State Update**: Records artifact hashes and timestamps.

## Output Artifacts

After successful completion, the following artifacts will be available:

- **Datasets**: `data/raw/`, `data/processed/`
- **Metrics**: `data/metrics/` (CSV files)
- **Results**:
 - Statistical results: `results/statistical_analysis.json`
 - Visualizations: `results/figures/`
 - Guidelines: `results/guidelines.md`
 - Sensitivity analysis: `results/sensitivity.md`
 - Pilot study: `results/pilot_study.md`
- **State**: `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`

## Troubleshooting

- **Error 101**: Amendment PRs not approved. Check `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` and ensure amendments are merged.
- **Error 102**: Dataset validation failed (e.g., < 95% valid AST parses). Check logs in `results/pipeline_validation.log`.
- **Error 103**: Length filtering failed to achieve comparable median lengths.
- **Error 104**: Insufficient valid snippets (< 1000 per group).

For detailed logs, check `results/pipeline_validation.log`.