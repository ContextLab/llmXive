# Quickstart Guide

This guide provides a one-command end-to-end run procedure for the **PROJ-488-evaluating-the-impact-of-code-generation** pipeline.

## Prerequisites

- Python 3.11+
- `git`
- Sufficient disk space (approx. 14 GB) for dataset storage
- Internet connection for downloading datasets

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-488-evaluating-the-impact-of-code-generation
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

## Constitutional Amendment Check

**CRITICAL**: Before running the pipeline, you must ensure that the required Constitutional Amendment PRs have been merged.

The pipeline requires:
- **Amendment VI**: Permission to use CodeParrot/CodeGen as the LLM-generated code source.
- **Amendment VII**: Permission to use `radon` and `pylint` for metric extraction.

The `code/main.py` script performs an automatic check against the state file (`state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`). If the amendments are not marked as `approved`, the pipeline will abort with an error code.

To manually verify the status, inspect the `amendment_status` section in the state file:
```bash
cat state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml
```
Ensure that both `amendment_vi` and `amendment_vii` are set to `approved`.

## One-Command Execution

To run the full pipeline (Data Ingestion -> Metric Extraction -> Statistical Analysis -> Visualization -> Guidelines), execute:

```bash
python code/main.py --run-all
```

This command will:
1. Verify the Constitutional Amendment status.
2. Download and verify datasets (CodeSearchNet, CodeParrot/CodeGen).
3. Filter and preprocess code snippets.
4. Extract static analysis metrics (radon, pylint).
5. Perform statistical comparisons (Mann-Whitney U, Cliff's Delta, BH correction).
6. Generate visualizations and review guidelines.
7. Update the project state file with artifact hashes and timestamps.

### Output Locations

- **Datasets**: `data/raw/`
- **Processed Metrics**: `data/metrics/`
- **Statistical Results**: `results/stats/`
- **Visualizations**: `results/figures/`
- **Guidelines**: `results/guidelines.md`
- **Pipeline Log**: `results/pipeline_validation.log`

## Troubleshooting

- **Amendment Check Failed**: If the pipeline aborts with an error regarding amendments, please ensure the PRs are merged and the state file is updated accordingly.
- **Dataset Download Errors**: Check your internet connection and ensure the HuggingFace `datasets` library is up to date.
- **Memory Issues**: If you encounter memory errors during processing, ensure you have sufficient RAM (minimum 8GB recommended).

## Verification

After the pipeline completes successfully, you can verify the results by checking the `results/guidelines.md` file and the generated figures in `results/figures/`. The `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` file will contain the latest hashes and timestamps for all artifacts.