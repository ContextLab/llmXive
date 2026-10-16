# Implementation Plan: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Branch**: `001-network-centrality-sleep-synchrony` | **Date**: 2026-10-15 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-network-centrality-sleep-synchrony/spec.md`

## Summary
Automate a reproducible pipeline that (1) downloads an open EEG sleep dataset, (2) preprocesses raw recordings (band‑pass filter 0.5–45 Hz, ICA artifact removal, 30 s epoching by sleep stage), (3) builds waking‑state functional connectivity matrices in theta (4–8 Hz) and alpha (8–13 Hz) bands, (4) extracts degree, betweenness, and eigenvector centrality, (5) computes Phase‑Lag Index (PLI) per sleep stage, (6) aggregates all per‑subject metrics into `SubjectMetrics.csv`, (7) checks collinearity across subjects (VIF), (8) validates that at least **30 subjects** have complete data **and** at least **2 min of clean wake** per subject, (9) selects Pearson or Spearman correlation (or partial correlation controlling for age, gender, total sleep time) based on normality, (10) applies Bonferroni correction across all tests, (11) validates the aggregated metrics file against the dataset schema, and (12) generates a JSON/Markdown report with all statistics and a “Confounding Limitation” section describing temporal proximity of waking and sleep recordings.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne==1.7.0`, `numpy`, `pandas`, `scipy`, `networkx`, `statsmodels`, `pyedflib`, `pytest`  
- **Storage**: Local filesystem under `data/` (raw, processed, metrics, results)  
- **Testing**: `pytest` (unit tests for each pipeline stage, integration test for end‑to‑end flow)  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ≤7 GB RAM) – CPU‑only  
- **Performance Goals**: Full run ≤ 4 h, peak RAM ≤ 4 GB  
- **Constraints**: No GPU; all steps must be CPU‑tractable; strict data‑hygiene (checksums, provenance).  

## Project Structure
```text
specs/001-network-centrality-sleep-synchrony/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md               # generated later

code/
├── __init__.py
├── config.yaml                # processing parameters, thresholds
├── download.py                # FR‑001
├── preprocess.py              # FR‑002
├── connectivity.py            # FR‑003
├── centrality.py              # FR‑004
├── pli.py                     # FR‑005
├── aggregate.py               # Aggregates results into SubjectMetrics.csv
├── vif.py                     # FR‑009 (global VIF across subjects)
├── analysis.py                # FR‑006, FR‑007, FR‑010, FR‑012, plus multivariate/partial correlation
├── validate.py                # validates SubjectMetrics.csv against contracts/dataset.schema.yaml
├── report.py                  # FR‑008, FR‑011
├── main.py                    # orchestration
└── requirements.txt

data/
├── raw/          # immutable .edf files
├── processed/
│   ├── epochs_{subj}.npz
│   ├── connectivity_{band}_{subj}.npy
│   └── pli_{stage}_{subj}.npy
├── metrics/
│   └── SubjectMetrics.csv          # aggregated per‑subject‑per‑stage metrics
└── results/
    └── analysis_results.json

tests/
├── unit/
│   ├── test_preprocess.py
│   ├── test_connectivity.py
│   ├── test_centrality.py
│   ├── test_pli.py
│   └── test_analysis.py
└── integration/
    └── test_pipeline.py
```

## FR/SC Coverage Matrix
| ID | Type | Plan Phase / Module | Status |
|----|------|---------------------|--------|
| FR-001 | Functional | `download.py` – uses `datasets.load_dataset` with SHA‑256 checksum verification. | Covered |
| FR-002 | Functional | `preprocess.py` – band‑pass (0.5–45 Hz), ICA (kurtosis > 5.0 **or** high‑freq > 3×baseline), 30 s epoching. | Covered |
| FR-003 | Functional | `connectivity.py` – coherence in theta & alpha bands, values ∈ (0, 1). | Covered |
| FR-004 | Functional | `centrality.py` – NetworkX degree, betweenness, eigenvector. | Covered |
| FR-005 | Functional | `pli.py` – PLI per epoch, mean global per stage, output ∈ [0, 1]. | Covered |
| FR-006 | Functional | `analysis.py` – per‑metric, per‑stage Pearson/Spearman/partial correlation (covariates: age, gender, total sleep time). | Covered |
| FR-007 | Functional | `analysis.py` – Bonferroni correction across all 30 tests. | Covered |
| FR-008 | Functional | `report.py` – JSON/Markdown report with all statistics. | Covered |
| FR-009 | Functional | `vif.py` – compute VIF across subjects for the three centrality predictors; flag global VIF > 5.0. | Covered |
| FR-010 | Functional | `analysis.py` – checks **N ≥ 30** subjects **and** ≥ 2 min clean wake per subject; halts with warning if not met. | Covered |
| FR-011 | Functional | `report.py` – adds “Confounding Limitation” if waking/night IDs match. | Covered |
| FR-012 | Functional | `analysis.py` – Shapiro‑Wilk test on each variable pair. | Covered |
| FR-013 | Functional | `validate.py` – validates `SubjectMetrics.csv` against `contracts/dataset.schema.yaml`. | Covered |
| SC-001 | Success | `download.py` + count comparison between raw & processed subjects. | Covered |
| SC-002 | Success | Runtime logged in `main.py`; target < 4 h. | Covered |
| SC-003 | Success | Memory profiling via `psutil` in `main.py`; target < 4 GB. | Covered |
| SC-004 | Success | Report ensures Bonferroni‑adjusted p < 0.05 for any claimed significance. | Covered |
| SC-005 | Success | Global VIF report included (FR‑009). | Covered |

## Computational Feasibility & Methodological Rigor
- **CPU‑first**: All steps use CPU‑only libraries. Processing is performed subject‑by‑subject to stay < 4 GB RAM.
- **Dataset Fit Warning**: The Hugging Face mirror `ronaldvandenbroek/physionet-sleep-data` provides the required EEG and sleep‑stage annotations, but wake segments are typically brief. We therefore **filter** for subjects with **≥ 2 min of clean waking data**. If the filtered pool yields fewer than **30 subjects**, the pipeline aborts with an “Insufficient Sample Size” warning (FR‑010). This mitigates the short‑wake limitation while staying within the open‑data constraint.
- **Multiple Comparisons**: Bonferroni correction across 3 centrality × 5 stages × 2 bands = 30 tests.
- **Power**: Minimum **N ≥ 30** subjects enforced (consistent with the original spec) to retain reasonable power for medium effects after correction.
- **Causal Claims**: Observational only; all statements are correlational (Constitution Principle VII).
- **Collinearity**: Global VIF computed across subjects; high VIF reported but not interpreted as independent effects.
- **Missing Sleep Stages**: Omit missing stage‑subject pairs from correlation (edge‑case handling).
- **Data Corruption**: Corrupted EDF files are logged, skipped, and checksum‑verified (FR‑001).
- **Temporal Confounding**: If waking and sleep recordings are from the same night, the report flags this limitation (FR‑011).
- **Covariate Adjustment**: Partial correlations control for age, gender, and total sleep time.

## Constitution Check
- **I. Reproducibility** – All steps are scripted, seeds pinned, and dataset fetched from a fixed URL.
- **II. Verified Accuracy** – No external citations introduced beyond the verified dataset URL.
- **III. Data Hygiene** – Checksums recorded; transformations write new files.
- **IV. Single Source of Truth** – Every figure/table derives from `SubjectMetrics.csv` or `analysis_results.json`.
- **V. Versioning Discipline** – Artifact hashes updated automatically by the pipeline.
- **VI. Signal‑Processing Transparency** – Parameters (bandpass, ICA thresholds, epoch length = 30 s) are stored in `code/config.yaml`.
- **VII. Statistical Rigor** – Bonferroni correction, normality testing, VIF diagnostics, and clear limitation statements are all implemented.
