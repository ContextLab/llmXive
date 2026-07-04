# Implementation Plan: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Branch**: `001-chemo-biomarker-discovery` | **Date**: 2024-01-15 | **Spec**: `specs/001-chemo-biomarker-discovery/spec.md`
**Input**: Feature specification from `/specs/001-chemo-biomarker-discovery/spec.md`

## Summary

This plan implements a reproducible, CPU‑only pipeline that (1) downloads ≥3 TCGA tumor‑type RNA‑seq datasets and ≥2 GEO microarray datasets with chemotherapy response annotations, (2) harmonizes gene identifiers, filters low‑expression genes, and normalizes counts via DESeq2 VST, (3) splits each tumor type into a **discovery** set (for differential expression) and a **training** set (for model fitting), (4) performs tumor‑type‑specific DESeq2 Wald tests on the discovery sets, (5) meta‑analyses significant genes across tumor types using Stouffer’s method, (6) builds elastic‑net logistic regression models **per tumor type** with nested cross‑validation, (7) validates models via leave‑one‑cancer‑type‑out (LOO) and external GEO cohorts, and (8) records all artifacts, runtime, and memory metrics to satisfy FR‑001 – FR‑014 and SC‑001 – SC‑006 while respecting the GitHub Actions free‑tier constraints.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `requests`, `tqdm`, `rpy2` (for DESeq2 and ComBat‑seq), `lifelines` (DeLong test), `joblib` (parallelism).
- **R Integration**: Used **only** for DESeq2 Wald test (FR‑005) and ComBat‑seq batch correction (FR‑014). If ComBat‑seq fails, the pipeline falls back to quantile matching (still compliant with FR‑014).
- **Randomness**: Fixed seeds in `src/config.py` guarantee reproducibility (Constitution I).
- **Compute Constraints**: No GPU, no large‑model training. All steps run within ≤6 h wall‑clock time and ≤7 GB RAM on the free‑tier runner.

## Constitution Check

| Principle | Satisfied? | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Deterministic seeds, fixed URLs, no manual steps. |
| II. Verified Accuracy | ✅ | All dataset URLs come from the verified block; no invented citations. |
| III. Data Hygiene | ✅ | Checksums recorded, immutable raw files, all transformations produce new files. |
| IV. Single Source of Truth | ✅ | All figures and statistics are generated from code outputs; `results/summary.md` is the sole human‑readable report. |
| V. Versioning Discipline | ✅ | Content hashes stored in `state/` after each phase. |
| VI. Cross‑Cohort Validation | ⚠️ | GEO validation requires ≥2 verified GEO datasets with response labels. If unavailable, the pipeline proceeds with internal validation only and records the limitation in `results/summary.md`. |
| VII. Statistical Rigor | ✅ | DE uses FDR < 0.05, meta‑analysis uses Bonferroni‑adjusted combined p‑values (m = panel size), ROC‑AUC ≥ 0.75 target, DeLong test, calibration checks, stratified CV with class weights for imbalance. |

## Project Structure

```
specs/001-chemo-biomarker-discovery/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── gene_panel.schema.yaml
│   ├── meta_analysis.schema.yaml
│   ├── metrics.schema.yaml
│   ├── model_output.schema.yaml
│   ├── sample.schema.yaml
│   ├── summary.schema.yaml
│   └── feasibility_gate.schema.yaml
└── tasks.md
src/
├── config.py
├── data/
│   ├── fetch.py          # T010‑T013
│   ├── preprocess.py     # T014‑T018
│   └── split.py          # T020
├── analysis/
│   ├── de_analysis.py    # T022‑T023
│   ├── meta_analysis.py  # T024‑T028
│   └── model.py          # T031‑T038
├── utils/
│   ├── logger.py
│   └── validators.py
└── cli.py
tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    └── test_analysis.py
data/
├── raw/
├── processed/
└── feasibility_gate.json
results/
├── summary.md
├── metrics.json
└── runtime_metrics.json
```

## Phases and Tasks

### Phase 0 – Data Acquisition & Feasibility Gate (US‑1)

| Task | Description |
|------|-------------|
| **T010** | Download TCGA RNA‑seq HTSeq‑Counts and clinical metadata for **≥3** tumor types via the TCGA API (FR‑001). |
| **T011** | Attempt download of **≥2** GEO microarray datasets with chemotherapy response annotations (FR‑002). If any dataset cannot be fetched **or** lacks a response label, write `data/feasibility_gate.json` with `status: "halted"` and `reason: "missing_geo"` and continue with internal validation only. |
| **T012** | Verify checksums; log a warning if total download size > 5 GB but continue (FR‑001). |
| **T013** | **Hard tumor‑type count gate**: after successful TCGA fetch, count distinct tumor types; if `<3`, write `data/feasibility_gate.json` (`status: "halted"`, `reason: "insufficient_tcga_types"`). |
| **T014** | Harmonize gene identifiers (Ensembl/Entrez → HGNC) retaining ≥95 % coverage (FR‑003). |
| **T015** | Filter low‑expression genes (CPM < 1 in > 80 % samples) (FR‑004). |
| **T016** | Apply DESeq2 Variance‑Stabilizing Transformation (VST) via rpy2 (FR‑004). |
| **T017** | **Batch correction**: attempt ComBat‑seq (R `sva` package) on the combined matrix (RNA‑seq counts). If ComBat‑seq fails (e.g., missing R package), fall back to quantile matching. Record which method was used (`batch_correction: "ComBat-seq"` or `"Quantile"`). |
| **T018** | Write processed files to `data/processed/` and generate `data/feasibility_gate.json` with `status: "ready"` if all checks pass. |

### Phase 1 – Discovery/Training Split & Differential Expression (US‑2)

| Task | Description |
|------|-------------|
| **T020** | For each tumor type, split the processed data **stratified by `response_label`** into a **Discovery** set ([deferred] of samples) for biomarker selection and a **Training** set ([deferred]) for model fitting (FR‑013). |
| **T021** | Verify class balance; if responder ratio < 20 %, log a warning and set `class_weights` for later modeling. |
| **T022** | Run DESeq2 Wald test **only on the Discovery set** (FR‑005). Output genes with FDR < 0.05 and |log2FC| > 1.0. |
| **T023** | Collect significant gene lists per tumor type. |
| **T024** | Compute the **intersection** of significant genes across **≥2** tumor types. |
| **T025** | **Fallback**: if the intersection is empty, create a **union** of the top‑ranked genes (≤50) across tumor types, write `fallback_reason: "intersection_empty"` into `results/summary.md`. |
| **T026** | Apply Stouffer’s method to combine p‑values for the candidate panel. |
| **T027** | Select the final gene panel: keep ≤ `config.MAX_VARIANCE_GENES` (default 50) most variable genes among the combined list. |
| **T028** | Save `results/meta_analysis/gene_panel.json` conforming to `contracts/gene_panel.schema.yaml`. |

### Phase 2 – Modeling & Validation (US‑3)

| Task | Description |
|------|-------------|
| **T031** | For each tumor type, train an elastic‑net logistic regression on the **Training set** using the fixed gene panel (FR‑007). Perform **nested 5‑fold CV**: inner CV tunes `alpha` and `lambda`; outer CV estimates performance. |
| **T032** | Record ROC‑AUC, precision‑recall curves, and calibration curves for each outer fold. |
| **T033** | **Leave‑One‑Cancer‑Type‑Out (LOO) validation**: train on N‑1 tumor types, test on the held‑out type. If after hold‑out fewer than 2 types remain, write `data/feasibility_gate.json` (`status: "halted"`, `reason: "insufficient_loo_types"`). |
| **T034** | **External GEO validation**: for each successfully downloaded GEO dataset, re‑normalize to the TCGA VST scale (using the same batch‑correction method recorded in T017), apply the trained per‑type model, and compute ROC‑AUC. If no GEO datasets are available, set `external_validation_status: "skipped"` in `results/summary.md`. |
| **T035** | Compute precision‑recall curves (store as list of `{precision, recall}`) and add to `results/metrics.json`. |
| **T036** | Generate calibration curves; for deciles with ≥20 samples, ensure deviation ≤ ±10 %; otherwise report CI and flag as ‘underpowered’. |
| **T037** | Perform DeLong’s test comparing each model against a clinical‑covariates‑only baseline; apply Bonferroni correction (m = number of model comparisons) with adjusted p‑value < 0.01 (FR‑011). |
| **T038** | Apply Bonferroni correction **only** to the meta‑analysis combined p‑values (m = size of the final gene panel) and to DeLong’s test p‑values (FR‑010). |
| **T039** | Aggregate all performance metrics into `results/metrics.json` (conforms to `contracts/metrics.schema.yaml`). |
| **T040** | **Resource monitoring**: enforce a 6‑hour wall‑clock timeout and a 7 GB RAM ceiling; write `results/runtime_metrics.json` with `timeout_triggered`, `peak_memory_mb`, and `runtime_seconds`. |

### Phase 3 – Reporting

| Task | Description |
|------|-------------|
| **T041** | Compile `results/summary.md` with overall status (`success`/`partial`/`halted`), gene panel size, any `fallback_reason`, `external_validation_status`, and a list of limitations (e.g., “missing GEO datasets”, “insufficient TCGA tumor types”, “power limitation”). |
| **T042** | Archive all artifacts, update `state/` hashes, and produce a final reproducibility report. |

## Success Criteria Mapping

| SC | Measured By |
|----|--------------|
| SC‑001 | AUC ≥ 0.75 on external GEO cohorts (if available) or on internal LOO validation (T033). |
| SC‑002 | Bonferroni‑adjusted p < 0.01 from DeLong’s test (T037). |
| SC‑003 | Performance drop between training and external validation recorded in `results/metrics.json`. |
| SC‑004 | `results/runtime_metrics.json` shows runtime ≤ 6 h. |
| SC‑005 | Same file reports peak memory ≤ 7 GB. |
| SC‑006 | `results/meta_analysis/` reports ≥2 tumor types contributing significant genes (T024). |

## Risk Management

- **Missing GEO response data**: If verified GEO datasets are unavailable, the pipeline proceeds with internal LOO validation and records the limitation (FR‑002, FR‑008). |
- **Memory spikes during DESeq2**: Process tumor types sequentially; limit gene set to top‑variance genes before DE when necessary. |
- **ComBat‑seq failure**: Automatic fallback to Quantile Matching ensures batch correction proceeds (FR‑014). |
- **Class imbalance**: Stratified CV always used; cost‑sensitive class weights applied when responder ratio < 20 % (FR‑009 edge case). |
- **Runtime overruns**: T040 monitors and aborts gracefully, writing `results/runtime_metrics.json` with `timeout_triggered`. |
