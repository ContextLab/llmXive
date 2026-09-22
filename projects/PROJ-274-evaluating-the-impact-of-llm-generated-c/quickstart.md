# Quickstart Guide

This guide outlines the commands to execute the project pipeline.
Ensure all prerequisites (Python 3.11+, dependencies) are installed.

## 1. Environment Setup

```bash
pip install -r requirements.txt
```

## 2. Project Initialization

Ensure directory structure and initial state files are created.

```bash
# Initialize project directories
python code/setup_project.py

# Initialize run metadata (Required for Phase 2 gates)
python code/utils/run_metadata.py
```

## 3. Data Collection & Experiment (Mock Mode)

Run a mock experiment to verify the logging pipeline.

```bash
python code/experiment/experiment.py --mode mock --participants 3
```

## 4. Documentation Generation

Generate documentation for a sample repository.

```bash
# Note: Replace <repo_url> and <commit> with real values
python code/generation/doc_pipeline.py --repo <repo_url> --commit <commit> --output data/processed/docs/repo_docs.md
```

## 5. Data Cleaning & Analysis

Run the cleaning pipeline and statistical analysis.

```bash
# Run cleaning pipeline
python code/run_cleaning_pipeline.py

# Run statistical analysis
python code/analysis/stats_runner.py --input data/processed/task_logs_anon.json --output data/processed/analysis_results.json
```

## 6. Verification

Verify all artifacts are present.

```bash
python code/utils/validator.py
```

## Troubleshooting

- **FileNotFoundError**: Ensure `python code/setup_project.py` has been run to create necessary directories.
- **Import Errors**: Ensure you are running from the project root or that `code/` is in your `PYTHONPATH`.
- **Missing Data**: Ensure previous pipeline stages (e.g., experiment, cleaning) have completed successfully.