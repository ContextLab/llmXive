# Quickstart: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with 7GB+ RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Data Ingestion
Run the ingestion script to download and link data:
```bash
python code/main.py --step ingest
```
*Expected Output*: `data/processed/linked_trials.csv`, `data/processed/ingest_metrics.json`.

### Step 2: Preprocessing & Valence/Ambiguity Derivation
```bash
python code/main.py --step preprocess
```
*Expected Output*: `data/processed/linked_trials.csv` (updated with valence/ambiguity), `state/linkage_status.json`.

### Step 3: Statistical Modeling
```bash
python code/main.py --step model
```
*Expected Output*: `state/model_results.pkl`, `state/model_convergence_metrics.json`, `state/vif_flag.json`.

### Step 4: Reporting
```bash
python code/main.py --step report
```
*Expected Output*: `reports/final_report.pdf` (includes sensitivity analysis), `reports/pii_scan.json`.

## Verification

- Check `reports/pii_scan.json` for PII compliance.
- Check `state/linkage_status.json` for data completeness.
- Check `state/vif_flag.json` for collinearity flags.
- Verify `reports/final_report.pdf` contains interaction plots, coefficient tables, and sensitivity analysis summaries.

## Troubleshooting

- **Missing Data**: If the pipeline halts with "Data Gap: Image files missing for >10% of trials", verify the source dataset URL.
- **Convergence Failure**: Check `state/model_convergence_metrics.json` for optimizer attempts. Simplify random effects if necessary.
- **GPU Errors**: If CUDA is required for valence inference, ensure the Kaggle fallback is configured (handled automatically by CI).
- **Schema Mismatch**: If the pipeline halts with "Schema Mismatch", the primary dataset lacks required fields (response_time, participant_id).
