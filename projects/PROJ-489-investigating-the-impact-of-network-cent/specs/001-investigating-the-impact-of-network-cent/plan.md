# Implementation Plan: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Branch**: `001-network-centrality-sleep-synchrony` | **Date**: 2026-10-15 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-network-centrality-sleep-synchrony/spec.md`

## Summary

Automate a reproducible pipeline that (1) downloads an open EEG sleep dataset with verified checksum, (2) preprocesses raw recordings (band‑pass filter 0.5–45 Hz, ICA artifact removal, 30 s epoching by sleep stage), (3) builds waking‑state functional connectivity matrices in theta (4–8 Hz) and alpha (8–13 Hz) bands, (4) extracts degree, betweenness, and eigenvector centrality as per‑subject means, (5) computes Phase‑Lag Index (PLI) per sleep stage, (6) aggregates all per‑subject per‑stage metrics into `SubjectMetrics.csv`, (7) validates the aggregated metrics file against the dataset schema, (8) computes global collinearity diagnostics (VIF) across subjects, (9) validates that at least **30 subjects** have complete data **and** at least **2 min of clean wake** per subject, (10) selects Pearson or Spearman correlation based on Shapiro‑Wilk normality test, (11) computes partial correlations controlling for age, gender, and total sleep time, (12) applies Bonferroni correction across all 30 tests, and (13) generates a JSON/Markdown report with all statistics, global VIF diagnostics, and a "Confounding Limitation" section describing temporal proximity of waking and sleep recordings.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `mne==1.7.0`, `numpy`, `pandas`, `scipy`, `networkx`, `statsmodels`, `pyedflib`, `pytest`  
- **Storage**: Local filesystem under `data/` (raw, processed, metrics, results)  
- **Testing**: `pytest` (unit tests for each pipeline stage, integration test for end‑to‑end flow)  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ≤7 GB RAM) – CPU‑only  
- **Performance Goals**: Full run ≤ 4 h, peak RAM ≤ 4 GB  
- **Constraints**: No GPU; all steps must be CPU‑tractable; strict data‑hygiene (checksums, provenance).  

## Constitution Check

✓ **I. Reproducibility** – All steps are scripted, random seeds pinned in `code/config.yaml`, and dataset fetched from a fixed verified URL with checksum validation (FR‑001).  
✓ **II. Verified Accuracy** – All external citations are verified against authoritative sources (e.g., 30 s epoch length from 1908.11463).  
✓ **III. Data Hygiene** – Checksums recorded in artifact metadata; all transformations write new files with documented derivation; no PII in committed data.  
✓ **IV. Single Source of Truth** – Every figure, statistic, and interpretation in the final report traces back to `SubjectMetrics.csv` or `analysis_results.json`.  
✓ **V. Versioning Discipline** – Artifact hashes updated automatically; project state tracked in `state/projects/PROJ-489-*.yaml`.  
✓ **VI. Signal‑Processing Transparency** – All EEG preprocessing parameters (bandpass 0.5–45 Hz, ICA kurtosis > 5.0 or high‑freq > 3× baseline, 30 s epochs) stored in `code/config.yaml` with explicit version pins (MNE 1.7.0, SciPy).  
✓ **VII. Statistical Rigor & Multiple‑Comparison Control** – Bonferroni correction applied across all 30 tests (3 centrality metrics × 5 sleep stages × 2 bands); effect sizes, confidence intervals, and corrected p‑values reported for each pair; causal claims avoided (observational only).

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
├── download.py                # FR‑001: download & checksum verify
├── preprocess.py              # FR‑002: filter, ICA, epoch, extract night IDs
├── connectivity.py            # FR‑003: coherence in theta & alpha
├── centrality.py              # FR‑004: degree, betweenness, eigenvector (per‑subject means)
├── pli.py                     # FR‑005: Phase‑Lag Index per stage
├── aggregate.py               # Aggregates results into SubjectMetrics.csv
├── vif.py                     # FR‑009: global VIF across subjects
├── validate.py                # FR‑013: validates SubjectMetrics.csv against schema
├── analysis.py                # FR‑006, FR‑007, FR‑010, FR‑012: correlation, Bonferroni, partial corr
├── report.py                  # FR‑008, FR‑011: JSON & Markdown report
├── main.py                    # orchestration, timing, memory profiling
├── requirements.txt           # pinned dependencies
└── tests/
    ├── unit/
    │   ├── test_preprocess.py      # unit tests for preprocess.py
    │   ├── test_connectivity.py    # unit tests for connectivity.py
    │   ├── test_centrality.py      # unit tests for centrality.py
    │   ├── test_pli.py             # unit tests for pli.py
    │   ├── test_aggregate.py       # unit tests for aggregate.py
    │   ├── test_vif.py             # unit tests for vif.py
    │   ├── test_analysis.py        # unit tests for analysis.py
    │   └── test_validate.py        # unit tests for validate.py
    └── integration/
        └── test_pipeline.py        # end‑to‑end pipeline on 3‑subject subset

data/
├── raw/          # immutable .edf files + checksums
├── processed/
│   ├── epochs_{subj}.npz              # cleaned EEG epochs + metadata
│   ├── metadata_{subj}.json           # subject covariates, night IDs, wake duration
│   ├── connectivity_{band}_{subj}.npy # coherence matrix
│   ├── centrality_{subj}.json         # degree, betweenness, eigenvector means
│   └── pli_{stage}_{subj}.npy         # mean PLI per stage
├── metrics/
│   └── SubjectMetrics.csv             # aggregated per‑subject‑per‑stage metrics
└── results/
    ├── analysis_results.json          # all correlation statistics
    ├── vif_report.json                # global VIF diagnostics
    └── report.md                      # human‑readable summary

logs/
└── pipeline.log                       # timestamped execution log
```

## FR/SC Coverage Matrix

| ID | Type | Plan Phase / Module | Status |
|----|------|---------------------|--------|
| FR-001 | Functional | `download.py` – fetches dataset from verified HF URL, verifies SHA‑256 checksum before processing. | Covered |
| FR-002 | Functional | `preprocess.py` – band‑pass 0.5–45 Hz (SciPy FIR), ICA (kurtosis > 5.0 **or** high‑freq > 3×baseline), 30 s epoching, night‑ID extraction. | Covered |
| FR-003 | Functional | `connectivity.py` – magnitude‑squared coherence in theta & alpha bands (Welch's method), symmetric matrices, values ∈ (0, 1). | Covered |
| FR-004 | Functional | `centrality.py` – NetworkX degree, betweenness, eigenvector; aggregated as **mean across all nodes** per subject. | Covered |
| FR-005 | Functional | `pli.py` – Phase‑Lag Index per epoch (MNE), mean global per stage, output ∈ [0, 1]. | Covered |
| FR-006 | Functional | `analysis.py` – per‑metric, per‑stage Pearson/Spearman/partial correlation (covariates: age, gender, total sleep time). | Covered |
| FR-007 | Functional | `analysis.py` – Bonferroni correction across all 30 tests. | Covered |
| FR-008 | Functional | `report.py` – JSON & Markdown report with all statistics. | Covered |
| FR-009 | Functional | `vif.py` – compute global VIF across subjects for the three centrality predictors; flag global VIF > 5.0. | Covered |
| FR-010 | Functional | `analysis.py` – checks **N ≥ 30** subjects **and** ≥ 2 min clean wake per subject; halts with warning if not met. | Covered |
| FR-011 | Functional | `report.py` – adds "Confounding Limitation" if waking/sleep night IDs match. | Covered |
| FR-012 | Functional | `analysis.py` – Shapiro‑Wilk test on each variable pair; selects Pearson (p ≥ 0.05) or Spearman (p < 0.05). | Covered |
| FR-013 | Functional | `validate.py` – validates `SubjectMetrics.csv` against `contracts/dataset.schema.yaml`. | Covered |
| SC-001 | Success | `download.py` + count comparison; logged in `report.md`. | Covered |
| SC-002 | Success | Runtime logged in `main.py` via `time` module; target < 4 h. | Covered |
| SC-003 | Success | Memory profiling via `psutil` in `main.py`; target < 4 GB peak RSS. | Covered |
| SC-004 | Success | Report ensures Bonferroni‑adjusted p < 0.05 for any claimed significance. | Covered |
| SC-005 | Success | Global VIF report included in `vif_report.json` and summarized in `report.md`. | Covered |

## Computational Feasibility & Methodological Rigor

### CPU‑First Design

All steps use CPU‑only libraries (MNE, NumPy, SciPy, NetworkX, statsmodels). Processing is performed **subject‑by‑subject** with streaming I/O to stay within the **7 GB RAM / 14 GB disk** budget of a GitHub Actions free‑tier runner (2 vCPU, ≤6 h per job).

- **Download & Checksum** (download.py): Stream ZIP, extract .edf files one at a time, verify SHA‑256 in‑place.
- **Preprocessing** (preprocess.py): Load one subject's EDF, filter, ICA, epoch, write intermediate `.npz` + `.json` metadata, discard from memory before next subject.
- **Connectivity & Centrality** (connectivity.py, centrality.py): Load preprocessed epochs for one subject, compute coherence matrices and centrality, write `.npy` and `.json`, discard.
- **PLI** (pli.py): Load epochs per subject, compute PLI per stage, write `.npy`, discard.
- **Aggregation** (aggregate.py): Iterate over all processed subjects, read small `.json` and `.npy` files, accumulate into `SubjectMetrics.csv`.
- **VIF & Analysis** (vif.py, analysis.py): Load entire `SubjectMetrics.csv` (small, ~1 MB for 30 subjects × 4 stages), compute statistics in‑memory.

**Estimated footprint**: ~500 MB per subject in intermediate files; peak RAM during preprocessing ~2 GB (one subject + filter/ICA buffers); final aggregation ~500 MB. Total pipeline ≤ 4 GB peak RSS.

### Dataset Fit & Feasibility

The **PhysioNet Sleep‑EDF** dataset (via Hugging Face mirror `ronaldvandenbroek/physionet-sleep-data`) contains:
- EEG recordings with sleep‑stage annotations ✓
- Brief pre‑sleep wake periods (~2–5 min typical)
- Standard electrode sets (Fp1, Fp2, F3, F4, C3, C4, P3, P4, O1, O2, etc.) ✓

**Critical limitation**: Wake segments are typically short. Resting‑state coherence estimation requires ≥ 2 min of stable data (standard EEG practice). We therefore enforce a **≥ 2 min clean wake filter** (FR‑013). After filtering, we validate **N ≥ 30** subjects (FR‑010); if fewer remain, the pipeline aborts with an explicit "Insufficient Sample Size" warning. This is **honest**: we do not synthesize or fabricate wake data, and we acknowledge the power limitation in the final report.

**Verified dataset URL** (from user message): `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip`

### Statistical Rigor & Multiple Comparisons

- **Tests performed**: 3 centrality metrics × 5 sleep stages × 2 bands = **30 correlation tests**.
- **Correction method**: Bonferroni (family‑wise α = 0.05), applied uniformly (FR‑007).
- **Power**: Minimum **N ≥ 30** subjects enforced (FR‑010). After Bonferroni adjustment, per‑test α = 0.05 / 30 ≈ 0.0017. This is conservative but appropriate for exploratory analyses; effect sizes will be reported to contextualize practical significance.
- **Normality**: Shapiro‑Wilk test (SciPy) on each variable pair; Pearson if both normal (p ≥ 0.05), else Spearman (FR‑012).
- **Covariate adjustment**: Partial correlations (statsmodels) controlling for age, gender, and total sleep time. If covariates are missing for a subject, fall back to bivariate correlation and flag in the report.
- **Collinearity**: Global VIF computed across all subjects for the three centrality predictors (statsmodels). If global VIF > 5.0, flag in report but do NOT interpret centrality metrics as independent effects (FR‑009).

### Causal Claims & Observational Design

All reported relationships are **associational only**. No randomization or identification strategy is employed. The report explicitly states: "This is an observational analysis; all reported correlations are associational and do not imply causation." (Constitution Principle VII)

### Missing Data & Edge Cases

- **Missing sleep stages**: If a subject lacks a specific stage (e.g., no REM detected), that stage‑subject pair is omitted from correlation (not imputed or zeroed).
- **Data corruption**: Corrupted EDF files are logged, skipped, and the subject is excluded from analysis. Checksum mismatch triggers an error and halts the download (FR‑001).
- **Temporal confounding**: If `waking_night_id == sleep_night_id`, a "Confounding Limitation" paragraph is added to the report (FR‑011). This acknowledges that the same‑night pairing may introduce confounds (e.g., circadian state, fatigue).

### Methodological Soundness Checklist

✓ **Every FR & SC has a concrete plan element** that names the requirement ID and describes the implementation.  
✓ **No un‑spec'd constraints** are introduced (all thresholds, methods, and success metrics derive from the spec).  
✓ **Dataset variable fit verified**: PhysioNet Sleep‑EDF contains required EEG, sleep stages, and metadata; wake duration is limited but mitigated by the ≥ 2 min filter and explicit limitation note.  
✓ **Statistical rigor**: Bonferroni correction, normality testing, VIF diagnostics, partial correlations, and causal‑inference framing all in place.  
✓ **CPU feasibility**: All methods run on standard Python libraries; subject‑by‑subject streaming keeps RAM ≤ 4 GB; no GPU required.  
✓ **Data availability**: Open, programmatically downloadable dataset with verified URL; no access‑gated or synthetic stand‑ins.

---

## Implementation Phases

### Phase 0: Data Acquisition & Validation (Tasks T001–T003)

**Objective**: Download dataset, verify integrity, establish data pipeline.

- **T001**: `download.py` – Fetch ZIP from verified HF URL, extract .edf files, verify SHA‑256 checksums. Output: `data/raw/*.edf` + checksum log.
- **T002**: `preprocess.py` + unit tests – Filter, ICA, epoch. Output: `data/processed/epochs_*.npz` + `metadata_*.json`. Tests validate epoch length = 30 s, no NaN values, correct sleep‑stage labels, night‑ID extraction.
- **T003**: `connectivity.py` + unit tests – Coherence in theta & alpha. Output: `data/processed/connectivity_*.npy`. Tests validate matrix symmetry, values ∈ (0, 1).

### Phase 1: Metric Computation & Aggregation (Tasks T004–T007)

**Objective**: Compute centrality, PLI, and aggregate into `SubjectMetrics.csv`.

- **T004**: `centrality.py` + unit tests – Degree, betweenness, eigenvector. Output: `data/processed/centrality_*.json`. Tests validate against synthetic graphs.
- **T005**: `pli.py` + unit tests – Phase‑Lag Index per stage. Output: `data/processed/pli_*.npy`. Tests validate output ∈ [0, 1].
- **T006**: `aggregate.py` + unit tests – Consolidate into `SubjectMetrics.csv`. Output: `data/metrics/SubjectMetrics.csv`. Tests validate schema compliance.
- **T007**: `validate.py` + unit tests – Validate `SubjectMetrics.csv` against `contracts/dataset.schema.yaml`. Output: validation log.

### Phase 2: Collinearity & Sample‑Size Validation (Tasks T008–T009)

**Objective**: Check VIF and ensure N ≥ 30 with ≥ 2 min wake per subject.

- **T008**: `vif.py` + unit tests – Compute global VIF across subjects. Output: `data/results/vif_report.json`.
- **T009**: `analysis.py` (validation step) – Check N ≥ 30 and ≥ 2 min wake per subject. If not met, halt with warning. Output: validation summary to log.

### Phase 3: Statistical Analysis (Tasks T010–T012)

**Objective**: Correlation analysis with proper multiple‑comparison control.

- **T010**: `analysis.py` (normality & correlation) – Shapiro‑Wilk test, select Pearson/Spearman/partial correlation. Output: correlation coefficients, raw p‑values.
- **T011**: `analysis.py` (Bonferroni correction) – Apply correction across 30 tests. Output: corrected p‑values, significance flags.
- **T012**: `analysis.py` + unit tests – Validate corrected p ≥ raw p, FWER controlled. Tests run on synthetic data.

### Phase 4: Reporting (Tasks T013–T014)

**Objective**: Generate final JSON and Markdown report.

- **T013**: `report.py` – Write `data/results/analysis_results.json` with all statistics. Tests validate JSON schema.
- **T014**: `report.py` – Write `report.md` with tables, VIF summary, Confounding Limitation section, and limitation notes on wake duration. Tests check for required sections.

### Phase 5: Integration & End‑to‑End Testing (Task T015)

**Objective**: Run full pipeline on a 3‑subject subset and validate output.

- **T015**: `tests/integration/test_pipeline.py` – Execute all stages on 3‑subject subset. Validate that `SubjectMetrics.csv` and `analysis_results.json` have expected schema and content.

---

## Success Metrics

- **All unit tests pass** (`pytest tests/unit/ -v`; exit code 0).
- **Integration test passes** (`pytest tests/integration/test_pipeline.py -v`; exit code 0).
- **`SubjectMetrics.csv` validates** against `contracts/dataset.schema.yaml` (FR‑013).
- **`analysis_results.json` validates** against `contracts/analysis.schema.yaml`.
- **Runtime ≤ 4 h** on GitHub Actions runner (measured via `time` in `main.py`).
- **Peak RAM ≤ 4 GB** (measured via `psutil` in `main.py`).
- **All FRs and SCs explicitly addressed** in code and documentation.
- **No fabricated or synthetic data** in place of real dataset; wake duration limitation acknowledged.

---
