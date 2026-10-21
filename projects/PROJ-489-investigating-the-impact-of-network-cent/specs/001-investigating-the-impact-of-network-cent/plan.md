# Implementation Plan: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Branch**: `001-network-centrality-sleep-synchrony` | **Date**: 2026-10-21 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-network-centrality-sleep-synchrony/spec.md`

## Summary
Automate a reproducible end‑to‑end pipeline that (1) downloads the open Sleep‑EDF dataset from a verified Hugging Face mirror, (2) preprocesses raw EEG (band‑pass 0.5–45 Hz, ICA artifact removal, 30‑second epoching by sleep stage), (3) builds waking‑state functional connectivity matrices in theta (4–8 Hz) and alpha (8–13 Hz) bands, (4) derives degree, betweenness, and eigenvector centrality **using EEG channels only** (Fpz‑Cz, Pz‑Oz) as the primary predictor, (4b) optionally includes peripheral EOG/EMG channels in a secondary sensitivity analysis, (5) computes Phase‑Locking Value (PLV) per sleep stage, (6) aggregates per‑subject‑per‑stage metrics into `SubjectMetrics.csv`, (7) validates the aggregated file against a schema, (8) assesses collinearity (VIF) and sample‑size adequacy, (9) **checks centrality stability both within the waking segment (split‑half ICC) and across states (waking vs N2 sleep ICC)**, (10) selects Pearson or Spearman correlation based on Shapiro‑Wilk normality (internal to FR‑006), (11) applies Bonferroni correction across the multiple hypothesis tests, (12) performs a **post‑hoc power analysis** to quantify the achievable power given N = 30, and (13) generates a JSON/Markdown report with all statistics, VIF diagnostics, ICCs, limitation notes, and explicit associational language.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne==1.7.0`, `numpy`, `pandas`, `scipy`, `networkx`, `statsmodels`, `pyedflib`, `psutil`, `pytest`  
- **Storage**: Local filesystem under `data/` (raw, processed, metrics, results)  
- **Testing**: `pytest` unit & integration suites  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ≤7 GB RAM, ≤6 h per job) – **CPU‑only**  
- **Performance Goals**: Full run ≤ 4 h, peak RAM ≤ 4 GB  
- **Constraints**: No GPU; strict data‑hygiene (checksums, provenance).  

## Constitution Check
| Principle | Satisfied? | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | All steps scripted, seeds pinned in `code/config.yaml`; dataset fetched from a fixed URL with checksum verification. |
| II. Verified Accuracy | ✅ | All external citations (e.g., epoch length = 30 s) verified against the provided source (1908.11463). |
| III. Data Hygiene | ✅ | Checksums recorded; each transformation writes a new file with provenance metadata; no PII. |
| IV. Single Source of Truth | ✅ | Every figure/table in the final report traces back to `SubjectMetrics.csv` or `analysis_results.json`. |
| V. Versioning Discipline | ✅ | Artifact hashes updated automatically; `state/projects/...yaml` tracks changes. |
| VI. Signal‑Processing Transparency | ✅ | Parameters stored in `code/config.yaml`; library versions pinned. |
| VII. Statistical Rigor & Multiple‑Comparison Control | ✅ | Bonferroni correction, normality testing, VIF diagnostics, centrality‑stability ICCs (both split‑half and cross‑state), explicit associational disclaimer, and post‑hoc power analysis are all implemented. |

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
├── config.yaml                # processing parameters, thresholds, random seeds
├── download.py                # FR‑001
├── preprocess.py              # FR‑002
├── connectivity.py            # FR‑003
├── centrality.py              # FR‑004 (EEG‑only primary, optional peripheral)
├── centrality_stability.py    # new: intra‑subject split‑half ICC & cross‑state ICC
├── pli.py                     # FR‑005
├── aggregate.py               # FR‑006 (aggregation) & FR‑013 (validation)
├── vif.py                     # FR‑009
├── analysis.py                # FR‑006, FR‑007, FR‑010, internal normality test
├── report.py                  # FR‑008, FR‑011
├── main.py                    # Orchestrates phases, logs runtime & memory
├── requirements.txt
└── tests/
    ├── unit/
    │   ├── test_preprocess.py
    │   ├── test_connectivity.py
    │   ├── test_centrality.py
    │   ├── test_centrality_stability.py
    │   ├── test_pli.py
    │   ├── test_aggregate.py
    │   ├── test_vif.py
    │   ├── test_analysis.py
    │   └── test_report.py
    └── integration/
        └── test_pipeline.py   # End‑to‑end on 3‑subject subset

data/
├── raw/          # immutable .edf files + checksums
├── processed/
│   ├── epochs_{subj}.npz
│   ├── metadata_{subj}.json
│   ├── connectivity_theta_{subj}.npy
│   ├── connectivity_alpha_{subj}.npy
│   ├── centrality_{subj}.json          # EEG‑only metrics
│   ├── centrality_periph_{subj}.json   # optional peripheral metrics
│   ├── centrality_icc_{subj}.json      # split‑half ICC values
│   ├── centrality_cross_state_icc_{subj}.json  # wake‑vs‑N2 ICC values
│   └── pli_{stage}_{subj}.npy
├── metrics/
│   └── SubjectMetrics.csv
└── results/
    ├── analysis_results.json
    ├── vif_report.json
    ├── centrality_stability.json
    └── report.md

logs/
└── pipeline.log
```

## FR/SC Coverage Matrix
| ID | Type | Plan Phase / Module | Status |
|----|------|---------------------|--------|
| FR-001 | Functional | `download.py` – fetches dataset from verified HF URL, verifies SHA‑256 checksum before processing. | Covered |
| FR-002 | Functional | `preprocess.py` – band‑pass (0.5–45 Hz), ICA (kurtosis > 5 or high‑freq > 3 × baseline), 30 s epoching, night‑ID extraction. | Covered |
| FR-003 | Functional | `connectivity.py` – magnitude‑squared coherence (theta & alpha) via Welch’s method, symmetric, values ∈ (0, 1). | Covered |
| FR-004 | Functional | `centrality.py` – **EEG‑only** graph (Fpz‑Cz, Pz‑Oz) to compute degree, betweenness, eigenvector; optional `--include-peripheral` adds EOG/EMG for sensitivity. | Covered |
| FR-005 | Functional | `pli.py` – Phase‑Locking Index across all channel pairs per epoch; mean global per stage ∈ [0, 1]. | Covered |
| FR-006 | Functional | `analysis.py` – Pearson/Spearman/partial correlation per centrality‑stage‑band pair, internal Shapiro‑Wilk normality test. | Covered |
| FR-007 | Functional | `analysis.py` – Bonferroni correction across 30 tests. | Covered |
| FR-008 | Functional | `report.py` – JSON & Markdown report with all statistics, VIF, ICC, limitation notes. | Covered |
| FR-009 | Functional | `vif.py` – global VIF for the three centrality predictors; flag > 5.0. | Covered |
| FR-010 | Functional | `analysis.py` – checks **N ≥ 30** and **≥ 2 min wake** per subject; halts with warning if not met. | Covered |
| FR-011 | Functional | `report.py` – adds “Confounding Limitation” if waking and sleep night IDs match. | Covered |
| FR-013 | Functional | `aggregate.py` + `validate.py` – validates `SubjectMetrics.csv` against `contracts/dataset.schema.yaml`. | Covered |
| FR‑014 | Functional | `centrality_stability.py` – split‑half ICC of centrality metrics across waking halves and cross‑state ICC (waking vs N2 sleep). | Covered |
| FR‑015 | Functional | **Post‑hoc power analysis** performed in `analysis.py` after multiple‑comparison correction. | Covered |
| SC-001 | Success | `download.py` logs % of subjects successfully processed (vs total). | Covered |
| SC-002 | Success | `main.py` records wall‑clock runtime; target < 4 h. | Covered |
| SC-003 | Success | `main.py` records peak RSS via `psutil`; target < 4 GB. | Covered |
| SC-004 | Success | Report flags only results with Bonferroni‑adjusted p < 0.05 as “Significant”. | Covered |
| SC-005 | Success | VIF report included; flag > 5.0. | Covered |
| SC-006 | Success | Centrality‑stability ICC values reported; flag ICC < 0.6 as “unstable”. | Covered |
| SC-007 | Success | **Power‑analysis note added**; acknowledges limited power with N = 30 and reports achieved power for each test. | Covered |
| SC-008 | Success | Cross‑state centrality ICC reported; flag ICC < 0.6 as “unstable across states”. | Covered |

## Computational Feasibility & Methodological Rigor

### CPU‑First Design
All steps rely on CPU‑only libraries. Processing is **subject‑by‑subject** with streaming I/O:

- **Download** streams the ZIP, verifies each file on‑the‑fly.  
- **Preprocess** loads a single EDF, filters, runs ICA, epochs, writes `.npz` + `.json`, then releases memory.  
- **Connectivity / Centrality / PLV** operate on one subject’s preprocessed data at a time.  
- **Centrality Stability** reads the waking segment twice (when ≥ 2 min) and also extracts N2 sleep epochs for cross‑state ICC.  
- **Aggregation** reads the small per‑subject JSON/NPY files to build `SubjectMetrics.csv` (≈ 1 MB for ≥ 30 subjects).  
- **Statistical analysis** loads the CSV entirely (well within RAM).  

Estimated peak RAM ≤ 3.5 GB; total disk ≤ 10 GB. No GPU required; therefore the pipeline fits the GitHub Actions free‑tier constraints.

### Dataset Fit & Limitations
- **Dataset**: PhysioNet Sleep‑EDF via Hugging Face mirror `ronaldvandenbroek/physionet-sleep-data`. The mirror provides raw EDF files, sleep‑stage annotations, and minimal metadata.  
- **Channel Availability**: The EDF files contain EEG (Fpz‑Cz, Pz‑Oz) plus auxiliary EOG and EMG channels. Primary centrality uses **only EEG channels** to preserve neural construct validity; a secondary analysis can include the auxiliary channels (`--include-peripheral`).  
- **Wake Segment Length**: Typical pre‑sleep wake is short (often < 2 min). We enforce a **≥ 2 min clean wake** filter (FR‑013). If after filtering fewer than 30 subjects remain, the pipeline aborts with an explicit “Insufficient Sample Size” warning and logs the shortfall. No synthetic data are fabricated.  
- **Open Access**: The dataset is directly downloadable via the verified URL; no credentials are required.

### Statistical Rigor
- **Multiple Comparisons**: Bonferroni correction across 30 tests (`p_corrected = min(p_raw * 30, 1.0)`).  
- **Power**: Minimum N ≥ 30 enforced; a **post‑hoc power analysis** (using `statsmodels.stats.power`) is computed for each observed effect size and reported (SC‑007). The analysis notes that with the current N and stringent correction, detectable power for medium‑sized effects is modest, and results are interpreted cautiously.  
- **Normality & Correlation Choice**: Shapiro‑Wilk test on each variable pair; Pearson if both p ≥ 0.05, otherwise Spearman (internal to FR‑006).  
- **Covariate Adjustment**: Partial correlation controlling for age, gender, total sleep time, **and any additional metadata fields present** (e.g., medication, sleep quality) using `statsmodels`. Missing covariates → fallback to bivariate correlation with a flag.  
- **Collinearity**: Global VIF computed across subjects; VIF > 5.0 flagged (FR‑009).  
- **Centrality Stability**: Split‑half ICC within waking (FR‑014) and cross‑state ICC between waking and N2 sleep (new FR‑014 extension); ICC < 0.6 flagged as unstable (SC‑006, SC‑008).  
- **Causal Claims**: All statements are explicitly labeled “associational” (Constitution Principle VII).  
- **Edge Cases**: Missing sleep stages are excluded from the specific correlation; no imputation.  
- **Data Corruption**: Corrupted EDF files are logged, skipped, and do not stop the run.  
- **Temporal Confounding**: Same‑night waking/sleep flagged in report.  

## Implementation Phases
| Phase | Tasks | Description |
|-------|-------|-------------|
| **Phase 0** | T001–T003 | Download dataset, verify checksums, preprocess (filter + ICA + epoch). |
| **Phase 1** | T004–T007 | Compute connectivity, EEG‑only centrality, PLV, aggregate metrics, validate CSV. |
| **Phase 1b** | T008 | **Centrality Stability Check** – split waking data for split‑half ICC **and** compute cross‑state ICC between waking centrality and N2‑stage centrality; store `centrality_cross_state_icc_{subj}.json`. |
| **Phase 2** | T009–T010 | Compute global VIF, verify N ≥ 30 & ≥ 2 min wake per subject. |
| **Phase 3** | T011–T014 | Normality testing (internal), correlation (Pearson/Spearman/partial), Bonferroni correction, **post‑hoc power analysis**. |
| **Phase 4** | T015–T016 | Generate JSON results, human‑readable Markdown report (including VIF, ICC, cross‑state ICC, limitation sections). |
| **Phase 5** | T017 | Integration test on 3‑subject subset; end‑to‑end verification. |

All tasks map directly to the FR/SC matrix above.

---



