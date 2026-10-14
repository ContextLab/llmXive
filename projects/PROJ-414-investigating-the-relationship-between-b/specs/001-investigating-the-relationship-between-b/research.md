# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview

A reproducible CPU-only pipeline: real fMRI timeseries from the single verified OpenNeuro parquet mirror → deterministic 100-block vertex parcellation → bandpass cleaning → sliding-window Ledoit-Wolf connectivity → **vertex-block connectivity descriptors** → PCA → conditional permutation+FDR association with whatever real behavioral metadata exists (expected to halt) → sensitivity sweep → NetworkX/Matplotlib figures → master manifest.

**Primary deliverable (re-scoped):** a descriptive characterization of time-varying vertex-block connectivity descriptors across the real subjects in the verified dataset. The skill-association stage is conditional and its halt path is the expected, planned-for outcome. **Construct-validity limitation stated up front:** the contiguous vertex blocks are not neuroanatomically or functionally meaningful regions; the computed efficiency/modularity/participation values are properties of an arbitrary vertex grouping ("vertex-block connectivity descriptors"), NOT of brain networks, and are never interpreted as such anywhere in this project.

## Dataset Strategy

| Role | Dataset | Verified URL | Loader | Expected Variables | Notes |
|------|---------|--------------|--------|--------------------|-------|
| Primary fMRI timeseries | OpenNeuro fsLR-64k parquet mirror (test split shard 1 of 16) | ` (dataset dict: `) | Direct URL download (`urllib`/`huggingface_hub.hf_hub_download`) + `pyarrow.ParquetFile` row-group streaming | BOLD timeseries on fsLR 64k surface vertices; subject/run identifiers; possibly task metadata | **The only verified OpenNeuro fMRI source.** Column inventory is inspected at download time; improvisation ratings, training years, and FR-011 covariates are NOT expected to be present — their absence is handled explicitly (see Dataset-Variable Fit). |
| FSL datasets (CUB-200 etc.) | — | ` etc. | — | — | **Not used**: these are few-shot *image-classification* datasets unrelated to FSL neuroimaging software; citing them for fMRI preprocessing would be a category error. |
| AFNI | No verified source found | — | — | — | Not used; no URL fabricated. |
| ROI atlas | No verified source found | — | — | — | Not downloadable from a verified source; a deterministic contiguous-vertex 100-block scheme on the fsLR surface is used instead (documented deviation; outputs labeled vertex-block descriptors). |

### Dataset-Variable Fit (explicit mismatch statement)

The study's ideal inputs — expert blind improvisation ratings, years of training, instrument/genre/practice/education covariates, and Improvisation-vs-Scripted labels — are **not verifiably present** in the only obtainable fMRI source. Per the planning rules this mismatch is stated rather than hidden: the association stage (FR-004/005/009/011) is implemented in full and executes on any real behavioral columns found at runtime; if none exist — the expected path — it halts with a clear data-mismatch message (mirroring the spec's missing-task-label edge case) and the report records the scope gap. **No behavioral scores will be synthesized.** The primary deliverable is the descriptive descriptor characterization, which the real data fully supports.

## Preprocessing (FR-002, Python adaptation)

1. Stream the parquet shard row-group by row-group (`pyarrow.ParquetFile.iter_batches`) — never load the full file.
2. For each subject/run: average fsLR vertices within each of 100 deterministic contiguous vertex blocks → `(timepoints × 100)` block matrix (new file; raw parquet untouched). These blocks are arbitrary groupings of vertices, not neuroanatomical regions.
3. Bandpass filter 0.01–0.1 Hz and detrend via a `nilearn.signal.clean`-equivalent numpy/scipy implementation (Butterworth filter, `scipy.signal`).
4. QC: per-volume amplitude/derivative outliers; flag subjects with >20% bad volumes for exclusion with a logged reason (spec edge case). A frame-wise-displacement proxy is computed from available motion columns if present; otherwise QC uses amplitude-based scrubbing, documented as such.

FSL/AFNI are not run: no verified installation source exists and the data are already spatially normalized CIFTI timeseries (motion correction, slice timing, MNI normalization are inapplicable to this representation). This is a documented deviation, not a silent substitution.

## Dynamic Connectivity & Vertex-Block Descriptors (FR-003)

- **Sliding window**: rectangular, default 45 s (window length in TRs derived from the dataset's TR; minimum 30 timepoints enforced), step 10 s.
- **Estimator**: per-window `sklearn.covariance.LedoitWolf` shrinkage on block timeseries → regularized covariance → Pearson correlation conversion.
- **Graph**: weighted undirected graph from the absolute-correlation matrix (all edges retained, no arbitrary threshold).
- **Descriptors** (`networkx`): global efficiency (`nx.global_efficiency` on weighted graph), modularity (Louvain, `nx.community.louvain_communities`, fixed seed), participation coefficient (standard formula over Louvain communities, node-averaged). **These are vertex-block connectivity descriptors — properties of an arbitrary vertex grouping, not of brain networks — and are labeled as such in every output.**
- Output: `data/derived/metrics_<subject>.csv` per the `network_metrics` contract.

## Dimensionality Reduction (FR-008)

Window-level descriptor vectors (global efficiency, modularity, participation coefficient, summarized per subject as window means and SDs) are stacked across subjects; PCA (`sklearn.decomposition.PCA`, fixed seed) retains components explaining ≥80% variance. Because the three descriptors are definitionally related (all derived from the same connectivity matrices), PCA components are treated as descriptors of descriptor-space structure; no independent-effects claim is made for individual descriptors (spec collinearity assumption).

## Power Analysis (FR-010, SC-005)

The power calculation is **matched to the actual test** — a continuous predictor in a multiple regression with permutation inference — rather than a two-group t-test: Cohen's d = 0.5 is converted to a correlation effect size r = d/√(d²+4) ≈ 0.243, and the required N to detect that partial correlation at α = 0.05 (two-tailed), power [deferred], is computed via `statsmodels.stats.power` (correlation/F-test framework, covariate degrees of freedom accounted for). **Abort scope:** if the available subject count is below the required N, the pipeline aborts **only the association stage** with a clear insufficient-power message (SC-005) and records the under-power warning in `results/power_analysis.json` and the manifest; the descriptive primary deliverable always completes. With a small real sample, the study may be under-powered; this is reported honestly rather than hidden.

## Conditional Association Analysis (FR-004, FR-005, FR-009, FR-011)

- **Skill proxy priority** (per spec): expert blind rating (if a real rating column exists) > task condition (Improvisation vs Scripted, if labels exist) > years of training (if present). If none exists — the expected path — halt with an explicit message and record the scope gap; downstream stages proceed.
- **Model**: OLS `PC_score ~ skill_proxy + age + fd + instrument_type + genre + practice_intensity + education`, including each covariate only when actually present in the data (FR-011's "when such metadata are present" clause).
- **Inference (Freedman–Lane)**: fit the full model; fit the reduced covariates-only model; permute the reduced-model residuals (1000 seeded permutations); add permuted residuals to the reduced-model fit to form permuted outcomes; refit the full model and record the skill-proxy coefficient under each permutation → null distribution → permutation p-value. Freedman–Lane is used because naive permutation of the raw proxy yields invalid p-values when covariates are in the model. Benjamini-Hochberg FDR is then applied across all tested PCs (FR-005, SC-003).
- **Null results** are reported and flagged as `null_result`, never treated as pipeline failure (spec edge case, SC-001).
- **Framing**: strictly associational; no causal claims (observational data, no randomization).

## Sensitivity Analysis (FR-006, SC-002)

Full re-run of connectivity → PCA (→ association if it ran) for window ∈ {30, 45, 60} s × step ∈ {5, 10} s (6 combinations, including the default). Output `results/sensitivity_summary.csv` with per-combination descriptor statistics and, if the association stage ran, correlation coefficients with their SD/range. If the association stage halted (expected path), the correlation-SD field is written as `not_computable_no_skill_proxy`, making SC-002's unmeasurability explicit rather than silently absent.

## Visualization (FR-007)

- **If real task-condition labels exist**: mean adjacency matrices per condition; NetworkX graph construction; Matplotlib rendering; edge width ∝ mean weight; node color ∝ Louvain community.
- **If no labels exist (expected path)**: a **single-group descriptive topology figure** of the mean vertex-block descriptor graph, clearly labeled as descriptive with no group comparison. A PC-1 median-split grouping is explicitly NOT used — PC-1 is derived from the same descriptors being visualized, so such a comparison would be tautological.
- Saved to `results/fig_network_topology.png`; the figure caption states the vertex-block, non-neuroanatomical nature of the nodes.

## Decision / Rationale (compute feasibility)

- **CPU-first everywhere**: parquet streaming, 100×100 connectivity matrices, NetworkX descriptors, OLS + 1000 Freedman–Lane permutations, 6-combo sensitivity sweep — all trivially fit 2 CPU / 7 GB / 6 h. No method in this plan has a GPU-only form, so the Kaggle escape hatch is not needed.
- **Why direct parquet download instead of `datasets.load_dataset("openneuro/ds000246")`**: that dataset id does not exist (this is why the previous T001 execution failed with exit=1). The verified parquet URL is downloaded directly and streamed — this is the redo of T001.
- **Why the re-scope**: the dependent variable (improvisation skill) has no construct instantiation in any verified dataset; the honest primary deliverable is the descriptive descriptor characterization, with the association machinery implemented and its halt path planned as the expected outcome.

## Statistical Rigor Checklist

- **Multiple comparisons**: BH-FDR across tested PCs (FR-005, SC-003).
- **Permutation testing**: 1000 permutations, seeded, **Freedman–Lane scheme** (valid under covariate adjustment).
- **Power**: a priori correlation/F-test-based analysis matched to the regression design; abort gates the association stage only; small-N limitation acknowledged.
- **Causal framing**: associational only.
- **Measurement validity**: fsLR CIFTI timeseries are a standard, validated fMRI representation; the deterministic vertex-block parcellation is a documented deviation from validated atlases and is listed as a limitation; all outputs are labeled vertex-block connectivity descriptors, never brain-network metrics.
- **Collinearity**: descriptors definitionally related; PCA used; components treated as descriptors.
- **Confound control**: all present covariates included; absent covariates reported as unavailable.

## Constitution Check

All seven principles addressed in `plan.md` (see its Constitution Check table). Principle VI and VII deviations (no FSL/AFNI execution; vertex-block rather than atlas parcellation; expected halt of the rating-based analysis) are recorded in Complexity Tracking and routed through the constitution amendment procedure (see plan.md's Constitution Amendment Routing), not silently ignored.