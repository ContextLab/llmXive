# Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Project ID**: PROJ-472 | **Spec**: `specs/001-investigating-the-impact-of-network-stru/`

## Research Question

How do anatomical brain network properties (node degree distribution, clustering
coefficient from diffusion-MRI structural connectomes) relate to neural avalanche
statistics (size, duration) measured from human resting-state EEG?

## Overview

This project implements a full, reproducible analysis pipeline that:

1. **Data acquisition (US1)** — downloads matched diffusion-MRI and resting-state
 EEG data from OpenNeuro (`ds004230` / `ds004231`, HCP-Aging) with SHA-256
 checksum verification, and builds a unified participant-indexed store.
2. **Metric computation (US2)** — computes structural graph metrics (mean degree,
 clustering coefficient, rich-club coefficient via NetworkX) and neural
 avalanche statistics (size, duration, power-law exponents via the `powerlaw`
 package with likelihood-ratio model comparison).
3. **Statistical association (US3)** — tests Spearman rank correlations between
 structural metrics and avalanche exponents with permutation-based FWE
 correction, VIF collinearity diagnostics, and a threshold sensitivity sweep.
 All findings are framed as **associational, not causal**.

## Directory Layout

```text
code/ # all pipeline source code
├── config.py # constants: dataset URLs, thresholds, seeds
├── main.py # pipeline orchestrator (sample-size gate, analysis)
├── data/ # US1: download, preprocessing, QC, storage
├── analysis/ # US2/US3: metrics, avalanches, fitting, stats, report
├── utils/ # logging, environment, checksum utilities
└── validation/ # compliance checker
data/
├── raw/ # immutable downloaded data +.checksums.json
├── processed/ # connectomes, cleaned EEG, routing state, QC outputs
└── results/ # metrics tables, statistics, final report
tests/ # pytest unit and integration tests
specs/001-investigating-the-impact-of-network-stru/
├── spec.md # authoritative requirements
├── plan.md # implementation plan
├── quickstart.md # run-book
└── contracts/ # output schemas
```

## Installation

See `specs/001-investigating-the-impact-of-network-stru/quickstart.md` for the
full run-book. In brief:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

MRtrix3 (`tck2connectome`) must be available on `$PATH` for the dMRI stage.

## Running the Pipeline

```bash
python code/main.py
```

The orchestrator enforces the sample-size gate (T029c): it reads
`data/processed/usable_subjects.json`, compares the count to `N_MIN` (10), and
writes `data/processed/routing_state.json` with `"status": "proceed"` or
`"limited"` (generating `data/results/insufficient_sample_report.md` in the
limited case). If no usable subjects exist the pipeline halts loudly rather
than producing fabricated results.

## Data Sources (real data only)

- dMRI: OpenNeuro `ds004230` (HCP-Aging)
- EEG: OpenNeuro `ds004231`
- Parcellation: HCP-MMP1.0 (Glasser et al. 2016), 360 parcels

No synthetic stand-ins are used for the primary analysis. Simulation is used
only for clearly-labelled unit-test fixtures.

## Key Outputs

- `data/results/metrics_combined.csv` — participant-level structural + avalanche metrics
- `data/results/correlations.csv` — Spearman + permutation-corrected results
- `data/results/collinearity_status.json` — VIF diagnostics
- `data/results/sensitivity_summary.csv` — threshold sweep ({0.70, 0.75, 0.80})
- `data/results/report.md` — final report (associational framing enforced)

## Notes

- All random processes use the pinned seed in `code/config.py` (`RANDOM_SEED = 42`).
- The pipeline is CPU-first; no CUDA is required.
- Target runtime ceiling: ≤ 6 hours on a 2-vCPU / 7 GB RAM runner.
