# Quickstart Guide: Evaluating the Impact of LLM-Generated Code Documentation

This guide outlines the steps to run the full pipeline for the project.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## 1. Project Setup

Ensure the directory structure is created (Task T001a):
```bash
python code/setup_project.py # If exists, otherwise manual mkdir
```

## 2. Citation Extraction (Task T070a)

Extract citations from research and plan documents:
```bash
python code/utils/citation_extractor.py
```
This generates `state/citations.yaml`.

## 3. Repository Selection & Metrics (Phase 2)

- Calculate Cyclomatic Complexity:
 ```bash
 python code/run_cc_collection.py
 ```
- Calculate Lines of Code:
 ```bash
 python code/run_loc_collection.py
 ```
- Evaluate Documentation Quality:
 ```bash
 python code/run_doc_quality_rubric.py
 ```
- Run Selection Gate:
 ```bash
 python code/run_repo_selection_gate.py
 ```

## 4. Experiment Execution (Phase 3)

- Run Mock Experiment:
 ```bash
 python code/experiment/experiment.py --mode mock --participants 3
 ```

## 5. Documentation Generation (Phase 4)

- Generate Docs:
 ```bash
 python code/generation/doc_pipeline.py --repo <repo_url> --commit <commit_hash> --output data/processed/docs/repo_docs.md
 ```

## 6. Data Cleaning & Analysis (Phase 5 & 6)

- Run Cleaning Pipeline:
 ```bash
 python code/run_cleaning_pipeline.py
 ```
- Run Statistical Analysis:
 ```bash
 python code/analysis/stats_runner.py --input data/processed/task_logs_anon.json --output data/processed/analysis_results.json
 ```

## Verification

Ensure all output files in `data/processed/` and `data/reports/` are generated.
Check `state/validation_log.json` for research validation status.