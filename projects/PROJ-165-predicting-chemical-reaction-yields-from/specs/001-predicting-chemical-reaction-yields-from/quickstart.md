# Quickstart: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## Prerequisites
- Python 3.11 or newer
- Git
- Access to a GitHub Actions free‑tier runner **or** a local Linux environment with ≥ 8 GB RAM and 2 CPU cores
- Internet connectivity (to download USPTO parquet and query NIST / PubChem APIs)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-165-predicting-chemical-reaction-yields-from

# 2️⃣ Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r src/requirements.txt
```

`src/requirements.txt` pins exact versions (e.g., `torch==2.3.0`, `rdkit-pypi==2023.9.5`, `ruff==0.4.1`).

## Running the Full Pipeline

```bash
python src/cli/main.py --run-full --seed 42
```

The command executes the following phases **in order**:

1. **Data Ingestion** – Downloads USPTO‑50k parquet, queries NIST & PubChem for IR/¹H‑NMR spectra, writes raw files to `data/raw/`, logs `ingestion_log.json` and `validation_status.json`.
2. **Early‑exit Check** – If fewer than 300 reactions have complete spectra or the API‑failure rate exceeds 80 %, the script aborts with a `DATA_INSUFFICIENT` error (FR‑014) and writes `validation_status.json`.
3. **Preprocessing & Splitting** – Resamples spectra, normalizes, generates fingerprints, performs scaffold‑based split, writes `train.parquet`, `val.parquet`, `test.parquet`, and `leakage_report.json`.
4. **Model Training** – Trains the attention model and three baselines, saves `model.pth` and `training_log.csv`.
5. **Evaluation** – Computes RMSE/MAE/R², Wilcoxon tests (Bonferroni‑corrected), permutation test, VIF, attention heatmaps, and peak‑alignment report. All results are stored in `data/artifacts/` as JSON and PNG files.

### Demo Mode (Alternative Data Strategy)
If the real ingestion fails the size threshold, you can run the pipeline on the bundled demo dataset:

```bash
python src/cli/main.py --run-full --seed 42 --demo
```

The demo dataset (`data/demo/`) contains a modest number of reactions with fully measured IR, ¹H‑NMR, and yields, allowing you to exercise the entire workflow and generate all artifacts (including attention heatmaps) on a small scale. Results will be clearly flagged as **illustrative**.

### Verifying Reproducibility
Re‑run with the same seed:

```bash
python src/cli/main.py --run-full --seed 42   # or with --demo
```

- Compare SHA‑256 hashes in `state/projects/PROJ-165-.../artifact_hashes.yaml`.  
- Confirm that `model.pth`, `training_log.csv`, and `evaluation_report.json` are **identical** (bit‑wise) to the previous run.

## Expected Outcome (when sufficient data exists)
- `leakage_report.json` indicates that no overlap was detected (SC‑no overlap).  
- `evaluation_report.json` contains RMSE/MAE/R² for all four models, Wilcoxon p‑values < 0.0167, permutation mean R² < 0.05, VIF ≤ 5, and ≥ 80 % overlap of top‑weighted spectral regions across the 90 %, 95 %, 99 % thresholds (SC‑003).  
- Attention heatmaps (`attention_plot_*.png`) highlight chemically meaningful bands; `peak_alignment_report.json` reports ≥ 80 % matches to NIST functional‑group frequencies (SC‑008).

## What Happens If Data Are Insufficient?
If the ingestion step cannot collect ≥ 300 reactions with **both** IR and ¹H‑NMR spectra (the current realistic situation given available open data), the pipeline will:
- Log the failure reason in `validation_status.json`.  
- Exit with status code 1 and message `DATA_INSUFFICIENT`.  
- **Automatically** switch to the demo dataset (`--demo`) and execute the full training/evaluation workflow on that set, clearly flagging the results as illustrative.

You can still explore the full workflow using the **demo mode** described above.

## Troubleshooting
- **Out‑of‑Memory**: Reduce batch size in `src/cli/main.py` (`--batch-size 16`).  
- **High API Failure Rate**: The NIST WebBook may throttle requests; increase `--api-retry-delay` (seconds) or run the ingestion step locally with a longer timeout.  
- **VIF > 5**: Adjust the stochastic noise parameters in `src/data/ingestion.py` (if using a simulated fallback) or consider dropping highly collinear condition features.  
- **Static‑analysis failures**: Run `ruff check src/` locally; fix any hard‑coded metric literals before committing.

---


