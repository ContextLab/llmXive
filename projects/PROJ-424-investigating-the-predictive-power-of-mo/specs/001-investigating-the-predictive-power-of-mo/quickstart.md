# Quickstart: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Prerequisites
- Linux (Ubuntu 22.04), Python 3.11+, ~7 GB RAM, ~14 GB disk, no GPU.

## Installation

```bash
git clone <project-repo>
cd projects/PROJ-424-investigating-the-predictive-power-of-mo
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
```

## Data Preparation

Verify `data/raw/nist_refs.json` contains entries for water, ethanol, acetone, e.g.:

```json
[
  {"solvent": "water", "temperature_kelvin": "ambient temperature",
   "diffusion_coefficient_m2_s": "to be estimated in the implementation phase, expected to be comparable to values reported in similar studies", "source_reference": "NIST"}
]
```

(Exact values are the manually curated committed file; do not edit in place.)

## Run the Pipeline (end‑to‑end, FR‑009 / SC‑006)

```bash
python code/pipeline.py            # simulations + analysis + reporting
# or stage by stage:
python code/simulations/run_simulation.py --solvents water ethanol acetone --durations 1 5 10 --seeds 3
python code/analysis/report.py
```

`pipeline.py` performs: simulation runs (seeded, fixed boxes containing on the order of a few hundred molecules) → MSD extraction with first 0.1 of time discarded → linear fit with R² ≥ 0.95 **and** log‑log slope check → Yeh‑Hummer finite‑size correction → D = slope/6 → MAE per solvent/duration → 1000‑iteration bootstrap CIs → descriptive paired‑comparison (granularity note) → sensitivity analysis over start fractions → figures and tables.

`results/` contains:
- `timescale_accuracy_curves.pdf` — MAE vs. duration with 95 % confidence bands, per solvent (SC‑001).
- `summary_statistics.md` — mean MAE, 95 % CI, trend commentary per solvent (SC‑004), and the descriptive paired‑comparison note (replaces the original p‑value) (SC‑005).
- `sensitivity_report.json` — variance percentages for start‑fraction sweeps (SC‑??? – added to satisfy methodological rigor).

## Verification Checklist

| Check | Where |
|-------|------|
| All accepted trajectories have R² ≥ 0.95 **and** log‑log slope ≈ 1 | `diffusion_results.csv` `r_squared` column; failures flagged `convergence_failed` |
| Bootstrap used a sufficiently large number of iterations. | `bootstrap_stats.json` `iterations` field = 1000 |
| 95 % CI present for every solvent × duration (or `null` with note) | `bootstrap_stats.json` `ci_lower`/`ci_upper` (may be `null` when no seeds accepted) |
| Sensitivity analysis output present | `sensitivity_report.json` |
| Paired‑comparison granularity note present | `bootstrap_stats.json` `paired_test` entries |
| End‑to‑end run without errors | Re‑run `python code/pipeline.py` from a clean checkout |

## Troubleshooting
- **OpenMM import fails** — reinstall from `code/requirements.txt` (conda‑forge wheel).
- **R² < 0.95 or log‑log slope out of range** — the trajectory is flagged, not silently dropped; inspect equilibration and MSD plot.
- **Wall‑clock > 5.5 h** — logged as a performance issue per FR‑004; bootstrap iterations are never reduced.
- **Null MAE/CI entries** — indicate that no seeds passed the convergence diagnostics; see the `granularity_note` in `bootstrap_stats.json` for interpretation.

---

