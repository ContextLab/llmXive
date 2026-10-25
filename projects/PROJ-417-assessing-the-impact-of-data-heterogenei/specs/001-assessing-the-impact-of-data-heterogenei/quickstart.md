# Quickstart: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Prerequisites
* Python 3.11 or newer  
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

# Install the exact, CPU‑only dependencies
pip install -r code/requirements.txt
```

`code/requirements.txt` contains:

```
numpy
pandas
scipy
matplotlib
pyyaml
pytest
jsonschema
```

## 3. Prepare the Synthetic Base Dataset

The pipeline creates a deterministic synthetic base that mimics realistic study‑size and SE distributions.

```bash
python code/scripts/generate_base.py --seed 42 --out data/processed/base_template.csv
```

The script uses a fixed random seed; if the file already exists it will be overwritten only after user confirmation.

## 4. Run the Full Simulation

```bash
# Full primary sweep (multiple τ² levels × 900 replicates) + sensitivity sweep
python code/main.py --mode full --seed 12345
```

**What happens**
1. `simulation/generator.py` creates replicates and writes `data/results/simulation_raw.jsonl`.  
2. `analysis/metrics.py` computes bias & coverage for each estimator.  
3. `analysis/stats.py` performs exact binomial tests (Bonferroni‑adjusted) and Kruskal‑Wallis tests for bias.  
4. `visualization/plots.py` writes `coverage_vs_tau2.png` and `mean_bias_vs_tau2.png`.  
5. `reporting/report_gen.py` creates `data/results/report.md` with the required “associational” label and a summary of REML failures from `reml_failures.json`.

## 5. Run a Quick Dry‑Run (Sanity Check)

```bash
python code/main.py --mode dry-run --replicates 10 --levels 0 0.1 --seed 42
```

*Creates only a few levels × 10 replicates* and finishes within seconds. Use this to verify that all files are produced and schemas pass.

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

All commands should exit with a success status. The validation step confirms that:
* `simulation_raw.jsonl` contains records matching the three contract schemas.  
* `aggregated_metrics.csv` matches `contracts/aggregated_metric.schema.yaml`.  
* PNG plots exist in `data/results/`.

## 7. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **MemoryError** | Batch size too large for the runner. | Reduce the batch size via `--batch-size` or run in dry‑run mode. |
| **REML convergence warnings** | Very high τ² with few studies. | Expected; failures are logged in `reml_failures.json` and excluded from coverage. |
| **Missing PNGs** | Plot script not executed. | Re‑run `python code/visualization/plots.py` or the full pipeline. |
| **Schema validation fails** | Schema changed after data generation. | Re‑run the full pipeline to regenerate files matching the updated schema. |
| **Base‑data generation fails** | Unhandled exception in `generate_base.py`. | Check that the script has write permission to `data/processed/` and that the seed is an integer. |