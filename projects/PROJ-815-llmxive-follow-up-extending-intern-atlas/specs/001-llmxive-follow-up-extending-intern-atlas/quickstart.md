# Quickstart: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

## Prerequisites

- Python 3.11+
- Git
- Access to the Intern-Atlas graph snapshot and Retraction Watch Database (assumed to be available in `data/raw/` or via configured environment variables).

## Setup

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-815-llmxive-follow-up-extending-intern-atlas
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify data availability**:
    Ensure `data/raw/intern_atlas_graph.json` and `data/raw/retraction_watch.csv` exist. If not, run the data fetching script (if provided) or download manually.

## Running the Pipeline

### Step 1: Extract Features
Run the extraction script to compute topological features and map retraction labels.
```bash
python code/run_extraction.py
```
*Output*: `data/processed/feature_dataset.csv`

### Step 2: Train & Validate Models
Run the training script to fit the topological and baseline models, perform permutation tests (n=100), and generate sensitivity analysis (cutoffs {0.3, 0.5, 0.7}).
```bash
python code/run_training.py
```
*Output*: `data/processed/model_results.json`, `data/processed/permutation_results.csv`, plots in `paper/results/`.

### Step 3: Verify Results
Check the generated `model_results.json` for:
- AUC-ROC comparison between Topological and Baseline models.
- Permutation test significance (observed AUC > mean_permuted + 2*std).
- VIF/MI stability flags.
- Threshold sweep FPR/FNR for {0.3, 0.5, 0.7}.

## Troubleshooting

- **"No ground truth labels found"**: The Retraction Watch database may not have entries for 2010-2018. Verify the data file and date range.
- **Memory Error**: If the graph is too large, the script will attempt to sample. Ensure the CI runner has at least 7GB RAM.
- **Missing DOI Matches**: The script will fallback to fuzzy matching. Check logs for the number of fallback matches.

## Testing

Run the unit tests to verify feature extraction logic:
```bash
pytest code/tests/
```