# Quickstart: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Prerequisites
* Python 3.11 or newer
* `git` (to clone the repository)
* Access to a terminal (local machine or GitHub Actions runner)

## 2. Installation

```bash
# Clone the repository (or navigate to the project root if already present)
git clone 
cd PROJ-417-assessing-the-impact-of-data-heterogeneity

# Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install the exact, CPU‑only dependencies
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

The pipeline downloads a verified OpenML meta‑analysis dataset and creates a cleaned template.

```bash
python code/scripts/fetch_openml.py   # downloads to data/raw/openml_4210.csv
python code/scripts/generate_synthetic_base.py   # creates data/processed/base_template.csv
```

## 4. Run the Full Simulation (Primary + Sensitivity Sweeps)

```bash
# Full primary sweep (a range of τ² levels × 900 replicates) + sensitivity sweep (3 τ² levels × 900 replicates)
python code/main.py --mode full --seed 12345
```

**What happens**
1. `simulation/generator.py` creates **7 200** replicates (4 500 primary + 2 700 sensitivity) and streams them to `data/results/simulation_raw.json` (JSON‑lines).  
2. `analysis/metrics.py` computes bias & coverage for each estimator.  
3. `analysis/stats.py` performs exact binomial tests (Bonferroni‑adjusted) and **Kruskal‑Wallis** tests for bias (no Shapiro‑Wilk step).  
4. `visualization/plots.py` writes `coverage_vs_tau2.png` and `mean_bias_vs_tau2.png`.  
5. `reporting/report_gen.py` creates `data/results/report.md` with the required “associational” label and a summary of REML failures from `reml_failures.json`.

The run finishes in **[deferred]** on the GitHub Actions free‑tier runner and uses **approximately a few gigabytes of RAM**.

## 5. Run a Quick Dry‑Run (Sanity Check)

```bash
python code/main.py --mode dry-run --replicates-per-level 10 --tau-values 0 0.1 --seed 42
```

*Creates only a limited number of replicates* and finishes within seconds. Use this to verify that all files are produced and schemas pass.

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

All commands should exit with status 0. The validation step confirms that:
* `simulation_raw.json` contains a large set of JSON lines, each matching `contracts/simulated_dataset.schema.yaml` **and** `contracts/estimation_result.schema.yaml`.  
* `aggregated_metrics.csv` matches `contracts/aggregated_metric.schema.yaml`.  
* PNG plots exist in `data/results/`.

## 7. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **MemoryError** | Batch size too large for the runner. | Reduce `--batch-size` (default 100) or run in `dry-run` mode. |
| **REML convergence warnings** | Very high τ² with few studies. | Expected; failures are logged in `reml_failures.json` and excluded from coverage. |
| **Missing PNGs** | Plot script not executed. | Re‑run `python code/visualization/plots.py` or the full pipeline. |
| **Schema validation fails** | Schema changed after data generation. | Re‑run the full pipeline to regenerate files matching the updated schema. |

---


