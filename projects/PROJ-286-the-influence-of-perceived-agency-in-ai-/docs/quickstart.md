# Quickstart Guide: The Influence of Perceived Agency in AI Interactions on Trust

This guide provides step-by-step instructions for setting up the local development environment, running the experiment interface, and executing the analysis pipeline for the "Perceived Agency" research project.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## 1. Environment Setup

### Clone the Repository
```bash
git clone <repository-url>
cd <project-root>
```

### Install Dependencies
Install all required Python packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Verify Installation
Run the linting checks to ensure the environment is correctly configured:
```bash
python -m code.experiment.tests.test_linting
```
*Note: This runs `black --check` and `flake8` to verify code formatting.*

## 2. Running the Experiment Interface

The experiment interface is built with Streamlit and allows participants to interact with the AI under different agency conditions (High, Low, Control).

### Launch the Application
From the project root, run:
```bash
streamlit run code/experiment/app.py
```

The application will open in your default web browser (typically at `).

### Experiment Flow
1. **Consent**: Participants review and accept the consent form.
2. **Randomization**: The system assigns a condition (High, Low, or Control) based on `code/experiment/randomization.py`.
3. **Task**: Participants complete the simulated decision-making task.
4. **Survey**: Participants complete the 12-item Lee & See (2004) Trust Scale and attention checks. [UNRESOLVED-CLAIM: c_3b06ff85 — status=not_enough_info]
5. **Export**: Data is automatically saved to `data/raw/` with a timestamped filename and SHA-256 checksum.

## 3. Executing the Analysis Pipeline

Once data has been collected (or using the synthetic data generator for testing), run the analysis pipeline.

### Generate Synthetic Data (Optional - for testing)
To test the pipeline without real participant data:
```bash
python code/analysis/synthetic_data.py --n 50 --output data/raw/synthetic_sample.csv
```

### Run the Full Analysis
Execute the main analysis script:
```bash
python code/analysis/run_analysis.py
```

This script performs the following steps:
1. **Data Cleaning**: Loads raw CSVs, handles missing values, and flags attention check failures (`code/analysis/data_cleaning.py`).
2. **ANOVA & Contrasts**: Performs One-Way ANOVA and planned directional contrasts (`code/analysis/contrasts.py`).
3. **Post-Hoc Tests**: Runs Tukey HSD tests with family-wise error rate adjustment (`code/analysis/pairwise.py`).
4. **Effect Sizes**: Calculates Cohen's d for all pairwise comparisons (`code/analysis/effect_sizes.py`).
5. **Sensitivity Analysis**: Sweeps participant exclusion thresholds (`code/analysis/sensitivity.py`).
6. **Report Generation**: Compiles all results into `docs/report.md`.

## 4. Validation & Testing

### Run Unit Tests
Ensure all components are functioning correctly:
```bash
pytest code/experiment/tests/
pytest code/analysis/tests/
```

### Validate Phase 0 Artifacts
Verify that research prerequisites (citations, power analysis) are valid:
```bash
python code/research/validate_phase0.py
```

## 5. Troubleshooting

- **Import Errors**: Ensure you are running commands from the project root directory.
- **Streamlit Port Conflicts**: If port 8501 is in use, add `--server.port <port>` to the streamlit command.
- **Missing Data Files**: Ensure `data/raw/` exists and contains CSV files if running the analysis pipeline.
- **Schema Validation Errors**: If data export fails, check that `specs/001-perceived-agency-trust/contracts/participant.schema.yaml` matches the collected data structure.

## 6. Next Steps

- **Data Collection**: Deploy the Streamlit app to a hosted environment (e.g., Streamlit Cloud) for participant recruitment.
- **Report Review**: Once analysis is complete, review `docs/report.md` for statistical findings and sensitivity analysis results.
- **Protocol Update**: Update `docs/protocol.md` with any deviations from the pre-registered analysis plan.