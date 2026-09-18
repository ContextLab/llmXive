# Quickstart Guide: Visual Priming Analysis Pipeline

This guide walks you through the end-to-end execution of the `PROJ-345` pipeline.

## 1. Environment Setup

Ensure you have Python 3.11 installed. Create a virtual environment and install dependencies:

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

Verify the environment:
```bash
bash scripts/verify_env.sh
```

## 2. Initialize Project State

The pipeline requires an initialized state file to track artifacts and checksums.

```bash
python code/run_state_init.py
```

This creates `state/projects/PROJ-345/state.yaml`.

## 3. Data Ingestion (User Story 1)

Download and process real IAT data from OSF.

```bash
python code/data/ingest.py
```

**Output**:
- `data/processed/linked_trials.csv`: Trial-level data linked to stimuli.
- `data/processed/ingest_metrics.json`: Metrics including `linked_metadata_percentage`.
- Logs will indicate if >10% images are missing (HALT) or if linkage is <90% (HALT).

## 4. Preprocessing & Modeling (User Story 2)

Run VAD inference, check confounding, and fit Linear Mixed-Effects Models.

```bash
python code/data/preprocess.py
python code/models/lmm.py
```

**Outputs**:
- `data/processed/stimulus_metadata.csv`: Valence scores.
- `data/processed/confounding_report.json`: Confounding checks.
- `state/model_convergence_metrics.json`: Convergence rates.

**Note**: This step requires human-rated ambiguity scores. If missing, the script will halt with a specific error message.

## 5. Reporting (User Story 3)

Generate the final PDF report with plots and sensitivity analysis.

```bash
python code/reports/generate_report.py
```

**Output**:
- `reports/final_analysis.pdf`: Contains interaction plots, coefficient tables, and limitations.
- `data/processed/sensitivity_analysis.csv`: Alpha sensitivity sweep results.

## 6. Validation

Run the full pipeline validator to ensure reproducibility:

```bash
python code/validation/validate_quickstart.py
```

## Important Notes

- **Real Data Only**: This pipeline does not support synthetic data generation for inputs. If real data sources are unreachable, the process will fail loudly.
- **Associational Findings**: All statistical outputs are framed as associational, not causal.
- **Ambiguity Constraint**: The model will not run without verified human-rated ambiguity scores.
