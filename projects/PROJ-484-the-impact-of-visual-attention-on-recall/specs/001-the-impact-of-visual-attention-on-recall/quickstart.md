# Quickstart: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

## Prerequisites

-   Python 3.11+
-   Git
-   Internet access (for dataset download)
-   10GB free disk space (for raw data and processing)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-484-the-impact-of-visual-attention-on-recall
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Data Download & Verification (Manual)

**Important**: The pipeline will fail if no verified dataset is found.
-   Check `research.md` for the status of the RSVP dataset and verify its availability *before* proceeding.
-   If a verified source is found, run:
    ```bash
    python code/download_data.py
    ```
-   If no verified source is found, the script will exit with an error. **Do not proceed.**

### 2. Preprocessing

```bash
python code/preprocess.py
```
-   This script will:
    -   Load raw data.
    -   Apply I-VT algorithm to extract fixations.
    -   Map stimulus IDs to valence.
    -   Merge participant STAI scores.
    -   Filter invalid trials.
    -   Output `data/processed/analysis.csv`.

### 3. Model Fitting

```bash
python code/model_fit.py
```
-   This script will:
    -   Load `analysis.csv`.
    -   Fit the mixed-effects logistic regression.
    -   Perform the Likelihood-Ratio Test.
    -   Check convergence.
    -   Output `artifacts/logs/model_results.json` and `artifacts/logs/convergence.log`.

### 4. Visualization

```bash
python code/visualize.py
```
-   This script will:
    -   Generate marginal effects plots.
    -   Output `artifacts/figures/marginal_effects.png`.

### 5. Full Pipeline (Optional)

```bash
python code/run_pipeline.py
```
-   Runs download, preprocess, model, and visualization in sequence.
-   **Warning**: This will fail if the dataset is not available.

## Testing

Run the unit tests to verify the logic:
```bash
pytest tests/
```

## Troubleshooting

-   **Error: "No verified dataset found"**: This is expected if the RSVP dataset is not in the verified list. Check `research.md` for updates.
-   **Error: "Convergence failed"**: The script will automatically retry with a simplified random effects structure and log the warning.
-   **Memory Error**: Ensure you are not loading the full dataset into memory. The pipeline uses streaming.
