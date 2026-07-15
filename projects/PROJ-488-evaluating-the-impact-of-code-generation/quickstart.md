# Quickstart Guide: Evaluating the Impact of Code Generation

This guide provides a one-command end-to-end execution workflow for the **llmXive** project **PROJ-488**.
It ensures all constitutional amendments are approved before running the pipeline.

## Prerequisites

- Python 3.11+
- `pip` and `venv`
- Internet access (for dataset downloads)

## 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## 2. Verify Constitutional Amendments

Before running the pipeline, ensure that the Constitutional Amendment PRs (T009, T010)
have been reviewed and merged. The script below will check the state file for approval.

Run the verification check:

```bash
python -c "from amendment_prs import main; main()"
```

**If this fails**, the pipeline is blocked. Check `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`
for the `amendment_status` map. Both `amendment-vi` and `amendment-vii` must be `approved`.

## 3. Run the Full Pipeline

Once amendments are approved, execute the full end-to-end analysis with a single command:

```bash
python code/main.py --run-all
```

This command performs the following steps in order:
1. **Ingestion**: Downloads CodeSearchNet and CodeParrot/CodeGen datasets (with backoff).
2. **Filtering**: Filters for Python snippets and balances length distributions.
3. **Metric Extraction**: Computes Radon and Pylint metrics (CPU-only).
4. **Statistical Analysis**: Runs Mann-Whitney U tests, Cliff's delta, and power analysis.
5. **Visualization**: Generates boxplots and saves them to `results/figures/`.
6. **Guidelines**: Generates review guidelines based on significant findings.
7. **State Tracking**: Updates `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` with artifact hashes.

## 4. Expected Outputs

After successful completion, the following artifacts will be available:

- **Data**: `data/processed/snippets/`, `data/metrics/`
- **Results**: `results/statistics.json`, `results/figures/`, `results/guidelines.md`
- **State**: `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` (updated with hashes)

## Troubleshooting

- **Error 101**: Dataset verification failed. Check internet connection and HuggingFace access.
- **Error 102**: AST parsing or metric validation failed. Check logs in `logs/`.
- **Error 103**: Median length difference could not be balanced. Check `data/processed/length_filter.log`.
- **Amendment Blocked**: If the state file indicates amendments are not approved, do not proceed until they are merged.