# Implementation Plan: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Branch**: `001-network-centrality-sleep-synchrony` | **Date**: 2026-10-21 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-network-centrality-sleep-synchrony/spec.md`

## Summary
Automate a fully reproducible end‑to‑end pipeline that (1) downloads the open Sleep‑EDF dataset from a verified Hugging Face mirror, (2) preprocesses raw EEG (band‑pass 0.5–45 Hz, ICA artifact removal, 30‑second epoching by sleep stage), (3) computes inter‑hemispheric coherence (theta 4–8 Hz and alpha 8–13 Hz) between channels Fpz‑Cz and Pz‑Oz for each subject (the waking predictor), (4) calculates Phase‑Locking Value (PLV) for each sleep stage, (5) aggregates per‑subject metrics (including coherence, PLV, and ICC stability of the coherence predictor), (6) validates sample size (N ≥ 50) and waking duration (≥ 2 min), (7) performs normality testing, selects Pearson or Spearman correlation, applies **Benjamini‑Hochberg FDR** correction across the **8 primary tests** (2 coherence metrics × 4 sleep stages), conducts an a‑priori power analysis targeting N ≥ 50, and (8) generates a JSON/Markdown report with all statistics, ICC diagnostics, temporal‑proximity notes, and explicit associational language.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne==1.7.0`, `numpy`, `pandas`, `scipy`, `statsmodels`, `networkx`, `pyedflib`, `psutil`, `pytest`  
- **Storage**: Local filesystem under `data/` (raw, processed, metrics, results)  
- **Testing**: `pytest` unit & integration suites  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ≤7 GB RAM, ≤14 GB disk) – **CPU‑only**  
- **Performance Goals**: Full run ≤ 4 h, peak RAM ≤ 4 GB  
- **Constraints**: Strict data‑hygiene (checksums, provenance), no GPU usage.

## Constitution Check
| Principle | Satisfied? | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | All steps scripted, seeds pinned in `code/config.yaml`; dataset fetched from a fixed URL with checksum verification. |
| II. Verified Accuracy | ✅ | All external citations verified against source 1908.11463. |
| III. Data Hygiene | ✅ | Checksums recorded; each transformation writes a new file with provenance metadata; no PII. |
| IV. Single Source of Truth | ✅ | Every figure/table in the final report traces back to a single row in `SubjectMetrics.csv` or a single entry in `analysis_results.json`. |
| V. Versioning Discipline | ✅ | Artifact hashes updated automatically; `state/projects/...yaml` tracks changes. |
| VI. Signal‑Processing Transparency | ✅ | Parameters stored in `code/config.yaml`; library versions pinned. |
| VII. Statistical Rigor & Multiple‑Comparison Control | ✅ | **Benjamini‑Hochberg FDR** correction applied across the 8 primary tests (as required by FR‑007). |

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
├── connectivity.py            # FR‑003 (coherence matrix)
├── coherence_icc.py           # FR‑015 (split‑half ICC for coherence)
├── pli.py                     # FR‑005
├── aggregate.py               # FR‑006 & FR‑013 (aggregation & validation)
├── analysis.py                # FR‑006, FR‑007, FR‑010, FR‑012, FR‑014 (partial correlation)
├── report.py                  # FR‑008, FR‑011
├── main.py                    # Orchestrates phases, logs runtime & memory
├── requirements.txt
└── tests/
    ├── unit/
    │   ├── test_download.py
    │   ├── test_preprocess.py
    │   ├── test_connectivity.py
    │   ├── test_coherence_icc.py
    │   ├── test_pli.py
    │   ├── test_aggregate.py
    │   ├── test_analysis.py
    │   └── test_report.py
    └── integration/
        └── test_pipeline.py   # End‑to‑end on a subset of subjects

data/
├── raw/          # immutable .edf files + checksums
├── processed/
│   ├── epochs_{subj}.npz
│   ├── metadata_{subj}.json
│   ├── coherence_{band}_{subj}.npy          # inter‑hemispheric coherence per band
│   ├── coherence_icc_{subj}.json           # split‑half ICC per band
│   └── pli_{stage}_{subj}.npy
├── metrics/
│   └── SubjectMetrics.csv
└── results/
    ├── analysis_results.json
    ├── coherence_icc_report.json
    └── report.md

logs/
└── pipeline.log
```

## FR/SC Coverage Matrix
| ID | Type | Plan Phase / Module | Status |
|----|------|---------------------|--------|
| FR-001 | Functional | `download.py` – fetches dataset from verified HF URL, verifies SHA‑256 checksum. | Covered |
| FR-002 | Functional | `preprocess.py` – band‑pass (0.5–45 Hz), ICA (kurtosis > 5 or high‑freq > 3 × baseline), 30 s epoching, night‑ID extraction. | Covered |
| FR-003 | Functional | `connectivity.py` – magnitude‑squared coherence between Fpz‑Cz and Pz‑Oz for theta & alpha bands; values ∈ (0, 1). | Covered |
| FR-004 | Functional | **Inter‑hemispheric coherence** (theta & alpha) used as waking predictor (average across epochs). | Covered |
| FR-005 | Functional | `pli.py` – Phase‑Locking Value across all channel pairs per epoch; mean global per stage ∈ [0, 1]. | Covered |
| FR-006 | Functional | `analysis.py` – Shapiro‑Wilk, Pearson/Spearman/partial correlation per coherence‑stage pair, BH correction, post‑hoc power. | Covered |
| FR-007 | Functional | **Benjamini‑Hochberg FDR** correction across the **8 primary tests** (as required by spec). | Covered |
| FR-008 | Functional | `report.py` – JSON & Markdown report with all statistics, ICC diagnostics, temporal‑proximity notes. | Covered |
| FR-010 | Functional | `analysis.py` – validates **N ≥ 50** subjects and **≥ 2 min** wake per subject; halts with warning if not met. | Covered |
| FR-011 | Functional | `report.py` – adds “Confounding Limitation” if waking and sleep night IDs match. | Covered |
| FR-012 | Functional | `analysis.py` – Shapiro‑Wilk normality test on each predictor‑outcome pair. | Covered |
| FR-013 | Functional | `aggregate.py` – filters out subjects with waking duration < 2 min; only retained subjects proceed. | Covered |
| FR-014 | Functional | `analysis.py` – partial correlation controlling for **medication status, sleep‑quality score, EEG‑noise level**; listwise deletion for missing covariates. | Covered |
| FR-015 | Functional | `coherence_icc.py` – split‑half ICC of theta and alpha coherence within the waking segment; proceeds only if ICC ≥ 0.6 (otherwise logs a stability warning). | Covered |
| SC-001 | Success | `download.py` logs % of subjects successfully processed (vs total). | Covered |
| SC-002 | Success | `main.py` records wall‑clock runtime; target < 4 h. | Covered |
| SC-003 | Success | `main.py` records peak RSS via `psutil`; target < 4 GB. | Covered |
| SC-004 | Success | Report flags only results with BH‑adjusted q < 0.05 as “Significant”. | Covered |
| SC-005 | Success | ICC report (`coherence_icc_report.json`) included; flags ICC < 0.6 as “unstable”. | Covered |

## Computational Feasibility & Methodological Rigor

### CPU‑First Design
All steps rely on CPU‑only libraries. Processing is **subject‑by‑subject** with streaming I/O:

- **Download** streams the ZIP, verifies each file on‑the‑fly.  
- **Preprocess** loads a single EDF, filters, runs ICA, epochs, writes `.npz` + `.json`, then releases memory.  
- **Connectivity** computes coherence for the two channels per band.  
- **ICC** recomputes coherence on the two halves of the waking segment (requires only two passes).  
- **PLV** computed per epoch, aggregated per stage.  
- **Aggregation** builds a ≤ 1 MB CSV for ≥ 50 subjects.  
- **Statistical analysis** loads the CSV entirely (well within RAM).  

Estimated peak RAM ≤ 3.5 GB; total disk ≤ 10 GB. No GPU required.

### Dataset Fit & Limitations
- **Dataset**: PhysioNet Sleep‑EDF via Hugging  Face mirror `ronaldvandenbroek/physionet-sleep-data`. It contains **only two EEG channels** (Fpz‑Cz, Pz‑Oz), which is sufficient for the inter‑hemispheric coherence predictor but **insufficient for graph‑theoretic centrality**. The plan therefore uses coherence as the waking predictor, matching the functional requirement after spec revision.  
- **Wake Length**: Enforced ≥ 2 min clean wake; subjects not meeting this are excluded. If fewer than 50 subjects remain, the pipeline aborts with an explicit “Insufficient Sample Size” warning (SC‑005). No synthetic data are fabricated.

### Statistical Rigor
- **Multiple Comparisons**: Benjamini‑Hochberg FDR across the 8 tests (2 coherence metrics × 4 sleep stages).  
- **Power**: A priori calculation (α = 0.05/8 ≈ 0.00625, desired power = 0.80, effect size ≈ 0.30) yields N ≈ 50 subjects. Enforced as minimum. Post‑hoc power reported per test.  
- **Normality & Correlation Choice**: Shapiro‑Wilk test; Pearson if both p ≥ 0.05, otherwise Spearman.  
- **Covariate Adjustment**: Partial correlation controlling for medication status, sleep‑quality score, EEG‑noise level; subjects missing any covariate are excluded (listwise deletion).  
- **ICC Stability**: Split‑half ICC for theta & alpha coherence; ICC ≥ 0.6 required to proceed without a stability warning (FR‑015).  
- **Edge Cases**: Missing sleep stages excluded from that stage‑specific correlation; no imputation.  
- **Data Corruption**: Corrupted EDF files are logged, skipped, and do not stop the run.  
- **Temporal Confounding**: Same‑night waking/sleep flagged in report.  
- **Observational Design** – No randomization; all statements are correlational.  

## Implementation Phases
| Phase | Tasks | Description |
|-------|-------|-------------|
| **Phase 0** | T001–T003 | Download dataset, verify checksums, preprocess (filter + ICA + epoch). |
| **Phase 1** | T004–T006 | Compute inter‑hemispheric coherence (theta & alpha) per subject; compute split‑half ICC for each band. |
| **Phase 2** | T007–T008 | Compute PLV per stage, aggregate per‑subject‑per‑stage metrics, filter subjects with insufficient wake. |
| **Phase 3** | T009–T014 | Normality testing, select correlation method, compute Pearson/Spearman/partial correlations, apply **BH** correction, perform a priori & post‑hoc power analysis, handle missing covariates (listwise deletion). |
| **Phase 4** | T015–T016 | Generate JSON (`analysis_results.json`) and Markdown (`report.md`) reports, including ICC diagnostics, temporal‑proximity notes, and power discussion. |
| **Phase 5** | T017 | Integration test on a 3‑subject subset; end‑to‑end verification. |

All tasks map directly to the FR/SC matrix above.

---


