# Quickstart: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Prerequisites
* **Operating System**: Linux (Ubuntu 22.04 recommended) – the CI runner uses this environment.  
* **Python**: 3.11 or newer.  
* **OpenMM**: Installable via `conda` or `pip` (`conda install -c conda-forge openmm`).  
* **Git**: To clone the repository.  

## Installation

```bash
# Clone the project repository
git clone https://github.com/your-org/PROJ-424-investigating-the-predictive-power-of-mo.git
cd PROJ-424-investigating-the-predictive-power-of-mo

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## Data Preparation

1. **Experimental reference data**  
   Verify that `data/raw/nist_refs.json` exists and contains entries for water, ethanol, and acetone. Example snippet:

   ```json
   [
     {
       "solvent": "water",
       "temperature_kelvin": 298.15,
       "diffusion_coefficient_m2_s": <value to be estimated during the implementation phase>,
       "source_reference": "NIST"
     }
   ]
   ```

2. **Generate simulation trajectories** (if not already present):

   ```bash
   python code/simulations/run_simulation.py \
       --solvents water ethanol acetone \
       --durations 1 5 10 \
       --seeds 5
   ```

   *The script*:
   * builds OPLS‑AA boxes of **≈120 molecules** (identical for all durations),
   * runs energy minimization + equilibration,
   * performs production runs for the requested durations,
   * enforces the 12 h per‑trajectory ceiling (any exceedance is logged as a performance issue),
   * logs the actual number of seeds used (a fixed small number unless a failure forces abort).

## Running the Full Analysis Pipeline

```bash
python code/analysis/analyze_all.py
```

This single command performs:

1. **MSD calculation** (discarding first [deferred] of time).
2. **Linear regression** with `$R^{2}` check; trajectories failing the check are flagged.  
3. **Diffusion coefficient computation** and MAE evaluation.  
4. **Bootstrap** (exactly 1000 iterations) of MAE; if the overall wall‑clock exceeds 5.5 h the run is **logged as a performance issue** but no iteration count is reduced.  
5. **Sensitivity analysis** across start fractions 0.1, 0.2, 0.3.  
6. **Result serialization** to the three data‑model files.

## Generating Figures & Tables

```bash
python code/analysis/generate_report.py
```

Outputs are written to `results/`:

* `timescale_accuracy_curves.pdf` – MAE vs. duration with 95 % confidence bands.  
* `sensitivity_cv_table.md` – CV values per solvent (must be < 5 %).  
* `summary_statistics.md` – Mean MAE, CI bounds, and descriptive trend commentary.

## Verification Checklist

| Check | How to verify |
|-------|---------------|
| All trajectories have `$R^{2} ≥ 0.95` | Open `data/processed/diffusion_results.csv` and confirm the `r_squared` column meets the threshold. |
| Sensitivity CV < 5 % | Inspect `data/processed/sensitivity_report.json`; every `variance_pct` must be `< 5`. |
| Bootstrap CI present | `bootstrap_stats.json` must contain `ci_lower` and `ci_upper` for each duration. |
| Seed count matches plan | `n_seeds` field in `bootstrap_stats.json` should be **5** (target). |
| End‑to‑end execution | Re‑run `python code/analysis/analyze_all.py` after a clean checkout; it should complete without errors (FR‑009, SC‑006). |

## Troubleshooting

* **OpenMM not found** – Install via `conda install -c conda-forge openmm` or ensure `python -c "import openmm"` works.  
* **Convergence failures** – If any `r_squared` < 0.95, increase the simulation duration or verify system equilibration; the script logs offending trajectories.  
* **Runtime exceeds 5.5 h** – The pipeline will **log a performance issue** (per FR‑004) but will continue to run the full 1000‑iteration bootstrap and all 5 seeds. Review the CI log for the warning.  
* **Simulation exceeds 12 h** – The `run_simulation.py` script aborts the offending trajectory, logs the event as a performance issue, and proceeds with remaining runs (system size is already fixed across durations).  

---

