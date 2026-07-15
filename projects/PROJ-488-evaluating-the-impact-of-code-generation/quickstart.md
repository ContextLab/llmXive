# Quickstart Guide: Evaluating the Impact of Code Generation

This guide provides a one-command end-to-end execution for the `PROJ-488-evaluating-the-impact-of-code-generation` pipeline.

## Prerequisites

1. **Python 3.11+** installed.
2. **Constitutional Amendments Approved**: This pipeline **MUST** only run after the following amendments are merged and recorded in the state file:
 - **Amendment VI**: Permitting CodeParrot/CodeGen datasets.
 - **Amendment VII**: Permitting `radon` and `pylint` for static analysis.

## Installation

```bash
pip install -r code/requirements.txt
```

## Verification of Amendment Status

Before running the pipeline, the system verifies that the required Constitutional Amendments (T009, T010) have been approved and recorded in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`.

If the amendments are not approved, the pipeline will abort with a clear error message indicating which amendment is missing.

## One-Command Execution

Run the entire pipeline (Ingestion -> Filtering -> Metrics -> Statistics -> Visualization -> Guidelines) with:

```bash
python code/main.py --run-all
```

This command performs the following steps automatically:
1. **Checks Amendment Status**: Validates that T009 and T010 are approved in the state file.
2. **Enforces CPU Guard**: Ensures no CUDA usage is attempted.
3. **Data Ingestion**: Downloads CodeSearchNet and CodeGen datasets.
4. **Preprocessing**: Filters for Python functions and aligns lengths.
5. **Metric Extraction**: Runs `radon` and `pylint` on all snippets.
6. **Statistical Analysis**: Performs Mann-Whitney U tests, Cliff's Delta, and BH correction.
7. **Visualization**: Generates boxplots.
8. **Guideline Generation**: Produces review guidelines based on significant results.
9. **State Updates**: Records hashes and timestamps for all artifacts.

## Output Locations

- **Metrics**: `data/metrics/`
- **Statistical Results**: `results/statistics/`
- **Figures**: `results/figures/`
- **Guidelines**: `results/guidelines.md`
- **State**: `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`

## Troubleshooting

- **Error 101 (Dataset Not Verified)**: Check network connectivity and HuggingFace access.
- **Error 102 (Parse Failure)**: Inspect `results/diagnostics/` for invalid snippets.
- **Amendment Not Approved**: Ensure T009 and T010 PRs are merged and the state file is updated.