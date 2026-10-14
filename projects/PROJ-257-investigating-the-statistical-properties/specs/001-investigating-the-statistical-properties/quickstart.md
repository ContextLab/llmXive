# Quickstart: Statistical Properties of Simulated Black Hole Mergers

## Prerequisites
- Python 3.11+, pip, git

## Installation
```bash
git clone <repo-url> && cd <repo>
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Running the Pipeline
```bash
python src/main.py
```

**Options**:
- `--download-only` – fetch and validate GWTC files (pipeline aborts on failure).
- `--skip-download` – assume valid GWTC files already exist in `data/raw/`.
- `--seed <int>` – override the pinned random seed (debugging only).

## Expected Outputs
- `data/results/data_availability.json` – status of GWTC downloads; pipeline aborts if any source is `unavailable`.
- `data/processed/obs_catalog.csv` (requires successful GWTC download).
- `data/processed/sim_catalog.csv` – synthetic population.
- `data/results/ks_results.json` – KS statistics, Bonferroni‑adjusted p‑values, sensitivity flags, and embedded power‑analysis details.
- `outputs/figures/mass_ratio_kde.png` and `outputs/figures/effective_spin_kde.png` (≥ 300 DPI).
- `data/results/final_report.md` – summary, limitations, and interpretation.

If `data/results/data_availability.json` reports any source as `unavailable`, the pipeline stops with an explicit error; no synthetic observational stand‑in is used.

## Verification
```bash
pytest tests/
```
Contract tests validate every artifact against the schemas in `specs/.../contracts/`.

## Troubleshooting
- **Download failures**: three exponential‑backoff retries; on persistent failure the pipeline aborts and prints the reason from `data_availability.json`.
- **Memory**: the default `samples_per_event` is 1000; reduce via `--samples-per-event` if needed (still well under the 7 GB limit).
