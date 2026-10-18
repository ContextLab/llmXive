# Quickstart: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Prerequisites
* Python 3.11 or newer
* `git` (to clone the repository)
* Access to a terminal (local machine or GitHub Actions runner)

## 2. Installation

```bash
# Clone the repository (or navigate to the project root if already present)
git clone <repository-url>
cd PROJ-417-assessing-the-impact-of-data-heterogeneity

# Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install the exact, CPU-only dependencies
pip install -r code/requirements.txt
```

`code/requirements.txt` contains only:

```
numpy
pandas
scipy
matplotlib
pyyaml
pytest
```

## 3. Prepare the Base Dataset

The pipeline downloads a verified real meta-analysis dataset (the BCG
vaccine meta-analysis, Colditz et al. 1994, as distributed with the R
package `metafor`) and stores it as the canonical base file.

```bash
python code/scripts/fetch_openml.py   # writes data/raw/cochrane_base.csv
```

The script raises `FileNotFoundError` (non-zero exit) if the download
fails; there is no synthetic fallback.

## 4. Run the Full Simulation

```bash
# Full primary sweep (5 tau^2 levels x 500 replicates)
python code/main.py --mode full --seed 12345
```

**What happens**
1. The generator creates replicates and writes `data/results/simulation_raw.json`.
2. `analysis/metrics.py` computes bias & coverage for each estimator.
3. `analysis/stats.py` performs exact binomial tests (Bonferroni-adjusted) and Kruskal-Wallis tests for bias.
4. `visualization/plots.py` writes `coverage_vs_tau2.png` and `mean_bias_vs_tau2.png`.
5. `reporting/report_gen.py` creates `data/results/report.md` with the required "associational" label and a summary of REML failures from `reml_failures.json`.

## 5. Run a Quick Dry-Run (Sanity Check)

```bash
python code/main.py --mode dry-run --replicates 10 --levels 0 0.1 --seed 42
```

*Creates only 2 levels x 10 replicates* and finishes within seconds. Use
this to verify that all files are produced and schemas pass.

## 6. Verify Outputs

```bash
# 1. List result files
ls -lh data/results/

# 2. Validate schemas
python code/main.py --validate-contracts

# 3. Run unit and integration tests
pytest tests/unit/
pytest tests/integration/
```

All commands should exit with status 0. The validation step confirms that:
* `simulation_raw.json` contains a large set of records matching the schema contracts.
* `aggregated_metrics.csv` matches `contracts/aggregated_metric.schema.yaml`.
* PNG plots exist in `data/results/`.

## 7. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **MemoryError** | Batch size too large for the runner. | Reduce the batch size or run in dry-run mode. |
| **REML convergence warnings** | Very high tau^2 with few studies. | Expected; failures are logged in `reml_failures.json` and excluded from coverage. |
| **Missing PNGs** | Plot script not executed. | Re-run `python code/visualization/plots.py` or the full pipeline. |
| **Schema validation fails** | Schema changed after data generation. | Re-run the full pipeline to regenerate files matching the updated schema. |
| **Base-data fetch fails** | Network unavailable or upstream moved. | The script exits non-zero by design; check the URL in `code/scripts/fetch_openml.py`. |