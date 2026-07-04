# Quickstart: The Influence of Chatbot Politeness on User-Perceived Quality

## Prerequisites

-   Python 3.11+
-   Git
-   14 GB free disk space
-   8 GB RAM (recommended for smooth operation)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-755-the-influence-of-chatbot-politeness-on-u
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Download and Score Data
This step downloads the datasets, computes politeness scores, and saves the processed data.
```bash
python code/01_download_and_score.py
```
-   **Output**: `data/processed/scored_dialogues.parquet`
-   **Time**: ~1-2 hours (depends on dataset size and CPU speed).

### Step 2: Fit CLMM Model
This step fits the Cumulative Link Mixed-Effects Model.
```bash
python code/02_fit_clmm.py
```
-   **Output**: `data/processed/clmm_results.csv`

### Step 3: Robustness & Subgroup Analysis
This step runs the LIWC analysis and subgroup checks.
```bash
python code/03_robustness_analysis.py
```
-   **Output**: `data/processed/robustness_results.csv`

## Verifying Results

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting

-   **Memory Error**: If you encounter OOM errors, reduce the batch size in `01_download_and_score.py` or sample the dataset.
-   **Model Convergence**: If the CLMM fails to converge, check `logs/convergence.log` for diagnostics. The script will automatically attempt a simplified model.
-   **Dataset Missing**: If Persona-Chat is missing, the script will proceed with EmpatheticDialogues and log a warning.
