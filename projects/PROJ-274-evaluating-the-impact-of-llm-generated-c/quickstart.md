# Quickstart Guide: Evaluating the Impact of LLM-Generated Code Documentation

This guide provides the commands to run the full pipeline end-to-end.
Execute these commands in order.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Execution Steps

### 1. Initialize Run Metadata (T010b)
**Purpose**: Generate `state/run_metadata.json` with RUN_ID, start_time, and project_version.
**Required before**: Phase 2 gates.

```bash
python code/utils/run_metadata.py
```

### 2. Verify Project Structure (T001b)
```bash
python scripts/verify_structure.py
```

### 3. Recruit Participants (T073b)
```bash
python scripts/mock_recruitment.py
```

### 4. Repository Selection & Metrics (Phase 2)
```bash
# Calculate Cyclomatic Complexity
python code/run_cc_collection.py

# Calculate Lines of Code
python code/run_loc_collection.py

# Evaluate Documentation Quality
python code/run_doc_quality_rubric.py

# Filter Repositories & Generate Rubric
python code/run_rubric_selection.py

# Run Selection Gate (Verifies T021f)
python code/run_repo_selection_gate.py

# Generate Covariates
python code/run_covariate_collection.py
```

### 5. Participant Assignment (T014b)
```bash
python code/experiment/assignment.py
```

### 6. Generate Documentation (Phase 4)
```bash
python code/generation/doc_pipeline.py --repo <repo_url> --commit <commit_hash> --output data/processed/docs/repo_docs.md
```

### 7. Run Experiment (Phase 3)
```bash
python code/experiment/experiment.py --mode mock --participants 3
```

### 8. Data Cleaning (Phase 5)
```bash
python code/run_cleaning_pipeline.py
```

### 9. Statistical Analysis (Phase 6)
```bash
python code/analysis/stats_runner.py --input data/processed/cleaned_dataset.csv --output data/reports/primary_analysis_results.json
```

### 10. Generate Final Report
```bash
python code/analysis/prepare_research_protocol.py
```

## Verification

After running the full pipeline, verify the following artifacts exist:
- `state/run_metadata.json`
- `data/raw/repo_selection_rubric.json`
- `data/processed/assignment_log.json`
- `data/raw/llm_docs/` (populated)
- `data/processed/cleaned_dataset.csv`
- `data/reports/primary_analysis_results.json`
- `data/reports/final_report.md`