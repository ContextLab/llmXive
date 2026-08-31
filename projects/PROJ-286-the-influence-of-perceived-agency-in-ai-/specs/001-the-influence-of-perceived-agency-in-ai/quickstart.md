# Quickstart: The Influence of Perceived Agency in AI Interactions on Trust

## Prerequisites

-   Python 3.11 or higher
-   `pip` (Python package installer)
-   `git`

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-286-the-influence-of-perceived-agency-in-ai-/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### Step 1: Validate Citations (Phase 0)
Ensure the Lee & See citation is verified against the Crossref API and source document..
```bash
python code/main.py --phase validate_citations
```
*Expected Output*: A log confirming the DOI matches the primary source and `data/processed/citation_log.json` is created.

### Step 2: Generate Power Analysis Report (Phase 0)
Calculate the required sample size.
```bash
python code/main.py --phase power_analysis
```
*Expected Output*: `docs/power_analysis_report.md` with N ≥ 159.

### Step 3: Simulate Experiment (Phase 1)
Generate a simulated dataset of participants.
```bash
python code/main.py --phase simulate --n <sample_size>
```
*Expected Output*: `data/raw/simulation_run_YYYYMMDD.csv`.

### Step 4: Run Analysis (Phase 2)
Execute the statistical pipeline (including manipulation checks and hierarchical testing).
```bash
python code/main.py --phase analyze --input data/raw/simulation_run_YYYYMMDD.csv
```
*Expected Output*: `data/processed/analysis_results.csv` and `docs/results_report.md`.

### Step 5: Run Sensitivity Analysis (Phase 2)
Sweep exclusion thresholds to verify robustness.
```bash
python code/main.py --phase sensitivity --input data/raw/simulation_run_YYYYMMDD.csv
```
*Expected Output*: `docs/sensitivity_report.md`.

## Testing

Run the unit tests to verify statistical logic:
```bash
pytest tests/
```

## Troubleshooting

-   **Import Errors**: Ensure you are in the virtual environment.
-   **Missing Data**: Run the `simulate` phase before `analyze`.
-   **Citation Failure**: If the citation validator fails, check internet connectivity or the DOI registry status.
