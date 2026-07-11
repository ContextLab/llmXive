# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Prerequisites

*   Python 3.11+
*   Git
*   (Optional) Virtual environment manager (e.g., `venv`, `conda`)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-507-the-influence-of-visual-salience-on-mora
    ```

2.  **Set up the environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

3.  **Verify dependencies**:
    ```bash
    python -c "import numpy, pandas, scipy, statsmodels, PIL; print('All dependencies installed.')"
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end on a CPU-only environment.

### Step 0: Dataset Verification
```bash
python code/data_prep.py --verify-only
```
*   **Output**: `data/raw/verified_dataset_info.json` or a "Data Gap Report".
*   **Note**: This step halts the pipeline if no verified dataset is found.

### Step 0.5: Human Coding Pilot
```bash
python code/human_coding.py
```
*   **Output**: `data/processed/human_coding_results.csv`.
*   **Note**: This step requires real human annotators for the pilot.

### Step 1: Data Preparation (Simulated or Real)
This step generates the manipulated stimuli.
```bash
python code/data_prep.py
```
*   **Output**: `data/processed/` directory containing low, medium, and high salience variants.
*   **Note**: If no raw images are present, this script will use a small set of default public domain images or generate synthetic placeholders.

### Step 2: Survey Simulation (Pilot)
This step generates synthetic participant data to test the analysis pipeline.
```bash
python code/survey_sim.py
```
*   **Output**: `data/survey/responses.csv` (or `.parquet`).
*   **Note**: This simulates the data collection phase. In a real deployment, this step would be replaced by importing data from a survey platform.

### Step 2.5: Survey Deployment Pilot
```bash
python code/survey_deploy.py
```
*   **Output**: `data/survey/pilot_responses.csv` with real human data.
*   **Note**: This step deploys a functional survey interface to a small group of real participants.

### Step 3: Statistical Analysis & Pipeline Validation
This step performs the **Linear Mixed-Effects Model (LMM)** and generates the report.
```bash
python code/analysis.py
```
*   **Output**: `data/analysis/results.json` and a console report.
*   **Validation**: The script will also run 'Positive Control' and 'Null Control' simulations to validate **pipeline sensitivity and specificity**.
    *   **Note**: This step validates that the *code* correctly detects effects and controls error rates. It does *not* validate the scientific hypothesis (that salience affects blame) which requires real empirical data.

### Step 4: Validation
Run the unit tests to ensure data integrity and manipulation success.
```bash
pytest tests/
```

## Troubleshooting

*   **Import Errors**: Ensure the virtual environment is activated and `requirements.txt` is up to date.
*   **Missing Images**: If the pipeline fails due to missing images, check `data/raw/`. The script expects at least one image file.
*   **Memory Errors**: The pipeline is optimized for <7 GB RAM. If issues persist, reduce the number of simulated participants in `survey_sim.py`.

## Next Steps

*   **Real Data Collection**: Replace `survey_sim.py` with an integration to a survey platform (e.g., Prolific, Qualtrics) to collect real human data.
*   **Real Image Source**: Replace the placeholder images with a verified subset of Visual Genome or another open dataset.
*   **Paper Draft**: Use the `data/analysis/results.json` to populate the `docs/paper_draft.md`.