# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

**Branch**: `001-gene-regulation` | **Date**: 2026-10-14 (revision 2) | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This plan delivers a CPU-only, reproducible pipeline that (1) downloads the **only verified, directly-downloadable OpenNeuro fMRI source available to this project** — the `clane9/openneuro-fslr64k` parquet mirror (real BOLD timeseries on the fsLR 64k surface) — (2) extracts vertex-block timeseries and applies Python-based cleaning (bandpass 0.01–0.1 Hz, motion/QC flagging), since the verified data are already spatially normalized CIFTI timeseries, (3) computes sliding-window functional connectivity with a Ledoit-Wolf regularized estimator and derives graph-theoretic descriptors (global efficiency, modularity, participation coefficient) — **explicitly labeled "vertex-block connectivity descriptors," not brain-network properties** (see Construct-Validity Limitations), (4) reduces descriptors with PCA, (5) runs the skill-association regression with Freedman–Lane permutation testing and FDR correction **only if real behavioral metadata exists**, (6) sweeps window/step parameters, (7) renders NetworkX/Matplotlib topology figures, and (8) writes the master manifest (`results/manifest.csv`) as the Single Source of Truth.

**Re-scoped primary deliverable (must be read before execution):** the previously planned HuggingFace mirrors `openneuro/ds000246` and `openneuro/ds001600` **do not exist** and are not in the verified list (rejected task T001 failed for this reason). The only verified OpenNeuro fMRI source is `clane9/openneuro-fslr64k`, which contains real fMRI timeseries but, to the best of verifiable knowledge, **does not contain improvisation-task labels, expert improvisation ratings, years-of-training, or the covariate metadata (instrument, genre, practice intensity, education)** that FR-004/FR-009/FR-011 require. The original research question (brain dynamics ↔ improvisation skill) therefore **cannot be tested** with obtainable data: the dependent variable has no construct instantiation. This plan accordingly designates as its **primary deliverable** a reproducible, descriptive characterization of time-varying vertex-block connectivity descriptors across the real subjects in the verified dataset. The skill-association stage is a **conditional secondary analysis**: it executes only if real behavioral columns are found at runtime, and its **halt-with-explicit-data-mismatch-message path is the EXPECTED outcome**, planned for explicitly — all downstream stages (descriptor sensitivity, figures, manifest, report) complete after it, recording the scope gap for spec revision. **No synthetic behavioral scores will ever be invented.**

## Construct-Validity Limitations (read before interpreting any output)

1. **Parcellation.** The deterministic 100-block contiguous-vertex scheme on the fsLR surface is **not a neuroanatomically or functionally meaningful parcellation**. The computed global efficiency, modularity, and participation coefficient are **"vertex-block connectivity descriptors"** — properties of an arbitrary grouping of vertices — and are NOT interpretable as properties of brain networks. Every table, figure, and report sentence derived from them carries this label; no brain-network interpretation is made anywhere in this project.
2. **Dependent variable.** No verified dataset contains improvisation skill ratings; the skill-association stage is expected to halt (see Summary).

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies** (pinned in `code/requirements.txt`): `numpy`, `pandas`, `scipy`, `scikit-learn>=1.3` (Ledoit-Wolf, PCA), `networkx>=3.2` (graph descriptors, Louvain communities), `statsmodels>=0.14` (OLS, power analysis), `matplotlib>=3.8`, `pyarrow` (parquet I/O), `huggingface_hub` (direct file download), `pytest`.
- **Storage**: files under `data/` (raw parquet, derived CSVs) and `results/` (tables, figures, manifest).
- **Testing**: `pytest` unit tests + contract tests validating outputs against `contracts/`.
- **Target Platform**: GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ~14 GB disk, ≤6 h, CPU-only).
- **Project Type**: batch scientific analysis pipeline (CLI entry point).
- **Performance Goals**: full pipeline on the real parquet shard completes in ≤6 h, ≤7 GB RAM (streamed row-group processing).
- **Constraints**: CPU-only; only the verified dataset URL may be fetched; no fabricated data.
- **Scale/Scope**: one verified fMRI parquet shard (test split, ~1/16 of the mirror), sequential subject processing.

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Data fetched from the single verified URL (`) with SHA-256 checksum recorded; random seeds pinned in `code/config.py`; pipeline re-runnable end-to-end on a fresh runner. |
| II. Verified Accuracy | No dataset URL outside the verified list is cited. AFNI and standalone ROI-atlas datasets have **no verified source** and are not cited; no URL is fabricated for them. |
| III. Data Hygiene | Raw parquet checksummed in `data/checksums.json`; every transformation writes a new derived file; no in-place modification; no PII committed. |
| IV. Single Source of Truth | `results/manifest.csv` (FR-012) records every subject, derived descriptor, available covariate, and statistical outcome; every figure/table traces to manifest rows. |
| V. Versioning Discipline | All artifacts content-hashed; project state timestamp updated on artifact change. |
| VI. Neuroimaging Preprocessing & Topology Integrity | **Deviation, routed through amendment (see Constitution Amendment Routing).** The verified data are pre-normalized CIFTI fsLR timeseries, so FSL/AFNI spatial preprocessing cannot be applied (FSL is not installable from any verified source). Bandpass filtering (0.01–0.1 Hz) is applied in Python. Parcellation uses a deterministic 100-block contiguous-vertex scheme (no verified atlas source exists); this deviates from the AAL/Schaefer requirement and all outputs are labeled vertex-block descriptors. Sliding-window (30–60 s, step 5–10 s) and descriptor definitions follow the principle's parameters. |
| VII. Statistical Rigor | Permutation testing (1000 permutations, Freedman–Lane) + Benjamini-Hochberg FDR (α = 0.05) across tested PCs; covariate control for age/FD and all available FR-011 covariates; a priori power analysis (FR-010) with abort **of the association stage only**; associational framing only. **Dependent-variable caveat:** expert blind ratings are not available in any verified source; the primary skill measure cannot be instantiated — flagged below and routed through amendment. |

## Project Structure

```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── roi_timeseries.schema.yaml
│   ├── network_metrics.schema.yaml
│   ├── pca_scores.schema.yaml
│   ├── regression_results.schema.yaml
│   └── manifest.schema.yaml
└── tasks.md   # generated later

code/
├── config.py               # pinned seeds, window/step params, URLs
├── requirements.txt
├── download_openneuro.py   # direct parquet download + checksum (fixes T001)
├── extract_rois.py         # fsLR vertex -> 100-block timeseries + bandpass + QC
├── connectivity.py         # sliding-window Ledoit-Wolf correlations
├── graph_metrics.py        # vertex-block connectivity descriptors
├── dimensionality.py       # PCA
├── analysis.py             # power analysis, regression, Freedman-Lane permutation, FDR
├── sensitivity.py          # window/step sweep
├── visualization.py        # NetworkX + Matplotlib figures
└── run_all.py              # CLI orchestrator

tests/
├── unit/
└── contract/
```

**Structure Decision**: single-project layout (`code/` + `tests/`) — a batch analysis pipeline, no service or UI components.

## Constitution Amendment Routing

The deviations from Constitution VI (no FSL/AFNI execution; vertex-block rather than AAL/Schaefer parcellation) and from Constitution VII's expert-blind-rating dependent variable (expected halt path) **cannot be resolved by a plan note** — a per-project constitution is amendable only through its own amendment procedure (open a PR; update the version line; record a Sync Impact Report). This plan therefore:

- **Routes the three deviations through that amendment procedure** and records them here as pending amendments, not silent flags.
- **Phase contingency:** Phases **1, 2, 3, 5, 6, and 7 are contingent on the amendment being ratified** — Phase 2 computes descriptors from Phase 1's vertex-block timeseries and Phases 3/6/7 consume Phase 2's outputs, so none of them can run while Phase 1 is blocked. Only **Phase 0** (verified download + column inventory), **Phase 4** (power analysis, reporting-only), and **Phase 8** (manifest of what was processed) execute unconditionally. If the amendment is rejected, the honest outcome is a Phase-0-only run whose report states that the question is unanswerable with verified data and constitution-compliant methods — that report is itself the deliverable requested by the re-scope.
- If the amendment is ratified, all phases execute as ordered below.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| No FSL/AFNI execution (deviates from FR-002, Constitution VI) | FSL/AFNI cannot be installed on the CI runner from any verified source, and the only verified fMRI data are already-normalized CIFTI timeseries, so motion correction/slice timing/MNI normalization are inapplicable. | Running FSL would require an unverifiable installer or fabricating a source; bandpass + QC in Python is the honest faithful form on real data. |
| Deterministic contiguous-vertex 100-block scheme instead of Schaefer/AAL | No verified atlas download source exists (verified list: "ROIs: NO verified source found"). | Citing an atlas URL would violate Principle II; the deterministic scheme is reproducible and documented, and its outputs are labeled vertex-block descriptors, never brain-network metrics. |
| Skill-association stage conditional; halt path is the expected outcome | No verified dataset contains improvisation ratings or training metadata; the spec's own edge-case rule requires halting with a clear message rather than proceeding on missing labels. | Fabricating ratings or silently substituting a different question would be rejected at the execution/fabrication gate. |

## Phase & Task Mapping (covers all FR/SC)

| Phase | Tasks (brief) | FR IDs | SC IDs |
|-------|---------------|--------|--------|
| **0. Data acquisition** | Download the verified parquet shard directly via its URL with `huggingface_hub.hf_hub_download`/`urllib`; record SHA-256 in `data/checksums.json`; inspect real columns and write `data/raw/column_inventory.json` listing which of `subject_id`, task labels, behavioral covariates actually exist. **Redo of rejected T001 — must exit 0.** | FR-001 (adapted to verified source) | SC-004 |
| **1. Vertex-block extraction & cleaning** *(amendment-contingent)* | Stream parquet row groups; map fsLR vertices to 100 deterministic contiguous blocks; compute mean signal per block per timepoint; bandpass filter 0.01–0.1 Hz; compute per-subject motion/QC proxy and flag exclusions (edge case: >20% bad volumes) with logged reasons. | FR-002 (Python adaptation), FR-003 input | SC-004 |
| **2. Dynamic connectivity & vertex-block descriptors** *(amendment-contingent)* | Sliding-window Pearson with rectangular window (default 45 s window, 10 s step, ≥30 timepoints), Ledoit-Wolf shrinkage; weighted undirected graphs; global efficiency, Louvain modularity, participation coefficient per window per subject — **labeled vertex-block connectivity descriptors throughout**. | FR-003 | — |
| **3. Dimensionality reduction** *(amendment-contingent)* | Stack window-descriptor vectors; PCA retaining components explaining ≥80% variance; save per-subject PC scores. | FR-008 | — |
| **4. Power analysis** (reporting-only; never aborts the pipeline) | A priori power analysis appropriate to the continuous-predictor regression design: Cohen's d = 0.5 mapped to a correlation effect size (r ≈ 0.243), required N computed for a partial-correlation/F-test at α = 0.05, target power [deferred]; write `results/power_analysis.json` with required vs. available N. **The FR-010 abort applies ONLY to the association stage (Phase 5)**; the descriptive primary deliverable always completes, with under-power recorded as a warning in the power report and manifest. | FR-010 | SC-005 |
| **5. Conditional association analysis** *(amendment-contingent)* | If (and only if) real behavioral columns exist in the downloaded data: OLS regression of PC scores on the best available skill proxy (expert rating > task condition > years of training, per FR-004 priority) with age, FD, and all present FR-011 covariates; **Freedman–Lane residual permutation** (1000 permutations, seeded) for p-values; Benjamini-Hochberg FDR across PCs; null results reported and flagged, never treated as failure. If no skill proxy exists — the expected path — halt this stage with an explicit logged data-mismatch message and record the scope gap in the report; downstream stages proceed. | FR-004, FR-005, FR-009, FR-011 | SC-001 (measurable only on the non-expected path), SC-003 |
| **6. Sensitivity analysis** *(amendment-contingent)* | Re-run phases 2–3 (and 5 if it ran) for window ∈ {30, 45, 60} s × step ∈ {5, 10} s; report mean, SD, and range of the descriptor values (and correlation coefficients if Phase 5 ran) in `sensitivity_summary.csv`. If Phase 5 did not run, the correlation-SD field is written as `not_computable_no_skill_proxy` (SC-002 explicitly unmeasurable on the expected path). | FR-006 | SC-002 (conditional) |
| **7. Visualization** *(amendment-contingent)* | If real task-condition labels exist: mean adjacency per condition, NetworkX graph construction, Matplotlib rendering, edge width ∝ weight, node color ∝ Louvain community. If no labels exist (expected path): a **single-group descriptive topology figure** of the mean vertex-block descriptor graph — **no group comparison and no PC-1 median split** (a PC-1 split would compare the descriptors to themselves, a tautology). | FR-007 (group comparison conditional on real labels) | — |
| **8. Reporting & manifest** | Write `results/manifest.csv` with every subject, all derived descriptors, available covariates, statistical outcomes (or the halt marker), and exclusion log; validate against `manifest.schema.yaml`; produce final report tables including the scope-gap statement. | FR-012 | SC-006 |

Phases are strictly ordered: data is downloaded before any consumption (Phase 0 → 1), descriptors computed before PCA (2 → 3), PCA before regression (3 → 5), all results before figures and the final report (5–6 → 7 → 8). Phase 4 never aborts the pipeline; its abort clause gates Phase 5 only.

## Compute Feasibility (CPU-first)

- **Memory**: parquet read in row-group batches; per-subject block matrices are (timepoints × 100) — tens of MB at most; connectivity windows are 100×100. Peak RAM well under 2 GB.
- **Runtime**: connectivity + descriptors for all subjects in the shard is minutes-to-tens-of-minutes on 2 cores; the 6-combination sensitivity sweep and 1000 permutations remain within the ≤6 h budget.
- **GPU**: nothing in this plan requires CUDA; no GPU escape hatch needed.

## Power Analysis

Required N is computed at runtime by `analysis.py` (FR-010) using a **correlation/F-test framework matched to the actual analysis** (continuous predictor in a multiple regression with permutation inference): Cohen's d = 0.5 is converted to r = d/√(d²+4) ≈ 0.243, and the required N for detecting that partial correlation at α = 0.05 (two-tailed), power [deferred], is computed via `statsmodels.stats.power` (correlation/F-test power, with covariate degrees of freedom accounted for). **Scope of the abort:** if the available subject count is below the required N, the pipeline **aborts only the association stage (Phase 5)** with a clear insufficient-power message (SC-005) and records the under-power warning in `results/power_analysis.json` and the manifest; the descriptive primary deliverable (Phases 1–3, 6–8) always completes. With a small real sample the study is likely under-powered; this is reported honestly rather than hidden.

## Scope gaps flagged for spec revision (not silently planned around)

1. **FR-001** names ds000246/ds001600, which have no verified downloadable source; the spec must be revised to name the verified parquet source.
2. **FR-002 (FSL/AFNI preprocessing)** cannot be executed: no verified installer source, and the only verified data are pre-normalized. Python bandpass + QC is substituted; the spec should be revised accordingly.
3. **FR-004/FR-009 primary outcome (expert blind ratings)** has no verified data source; SC-001 is unmeasurable on the expected path. The association stage is implemented but expected to halt; the spec's data-availability assumption is false and must be revised (or the research question reformulated to the descriptive deliverable this plan designates as primary).
4. **Constitution VI parcellation (AAL/Schaefer)** has no verified download source; a deterministic 100-block contiguous-vertex scheme is used, documented, and routed through the constitution amendment procedure.
5. **FR-007/SC-002 fallbacks**: with no task labels, the visualization is single-group descriptive (no group comparison), and SC-002's correlation SD is reported as not-computable; the spec should define these fallbacks.