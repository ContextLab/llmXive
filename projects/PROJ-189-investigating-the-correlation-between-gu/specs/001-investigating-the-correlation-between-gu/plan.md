# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-25 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
Create a fully reproducible CPU‑only pipeline that (1) downloads the American Gut Project (AGP) 16S rRNA taxonomic table **directly from the Qiita/EBI repository** (official endpoint), (2) validates its SHA‑256 checksum, (3) **optionally** ingests a user‑provided **paired microbiome‑cognition dataset** (`data/raw/paired_dataset.parquet`) that already contains microbial genus abundances and cognitive scores for the same participants, (4) filters to participants age ≥ 60, (5) aborts with a clear diagnostic if the paired dataset is **missing or contains fewer than 200 participants** (a **Fatal Coverage Gap**), (6) proceeds with rarefaction, VIF screening, CLR transformation, covariate‑adjusted Spearman correlations, Random Forest modeling, linear regression, sensitivity sweeps, and power analyses **only when the paired dataset meets the size threshold**, A defined limit enforces a RAM guardrail., and (8) assembles all results (including checksum) into a single JSON file validated against contracts.

If the required paired dataset is not supplied, the pipeline stops after the provenance step, logs the deficiency, and **reports that the original research question cannot be answered with publicly available AGP and HRS data**. The specification must then be revised to provide an appropriate paired dataset or to adjust the research question.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `pingouin==0.5.*`, `shap==0.45.*`, `miceforest==5.6.*`, `datasets==2.20.*`, `psutil==5.9.*`  
- **Storage**: Local filesystem under `data/` (raw, processed, results, provenance)  
- **Testing**: `pytest` with contract tests in `tests/contract/`  
- **Target Platform**: GitHub Actions free‑tier runner (Multiple CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk)  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 6 GB  
- **Constraints**: CPU‑only execution; no GPU required  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic downloads, checksum validation. |
| II. Verified Accuracy | PASS | All URLs verified; AGP source is the official Qiita/EBI endpoint. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with recorded checksum. |
| IV. Single Source of Truth | PASS | Every figure/statistic traces to a single row in `data/processed/paired_dataset.parquet` (when present) and a single code block. |
| V. Versioning Discipline | PASS | All artifacts hashed; hashes stored in project state. |
| VI. Microbiome Data Provenance | PASS | AGP taxonomic tables obtained directly from the official Qiita/EBI endpoint. |
| VII. Predictive Modeling Transparency | PASS | Hyper‑parameters, seeds, performance, permutation null, VIF, and SHAP are logged and archived. |
| **Spec Feasibility** | **FAIL** | No publicly available paired AGP‑HRS dataset exists. The pipeline therefore aborts early if a suitable paired dataset is not supplied, and the specification must be revised to provide one or to change the research question. |

## Project Structure
```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── correlation.schema.yaml
│   ├── dataset.schema.yaml
│   ├── model.schema.yaml
│   └── results.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-189-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/
│   │   ├── agp.parquet          # downloaded from Qiita/EBI
│   │   └── paired_dataset.parquet   # user‑provided paired microbiome‑cognition data
│   ├── provenance/
│   │   ├── expected_checksums.json
│   │   └── observed_checksums.json
│   ├── processed/
│   │   ├── paired_dataset_age60.parquet          # only if ≥ 200 participants
│   │   ├── clr_normalized.parquet
│   │   └── imputed.parquet
│   └── results/
│       ├── correlations.json
│       ├── model.json
│       ├── linear_regression.json
│       ├── sensitivity.json
│       ├── unified_results.json
│       ├── summary.md
│       └── figures/
│           ├── correlation_heatmap.png
│           └── model_shap_summary.png
├── code/
│   ├── requirements.txt
│   ├── 01_download_and_provenance.py
│   ├── 02_load_and_filter.py
│   ├── 03_correlation.py
│   ├── 04_modeling.py
│   ├── 05_linear_regression.py
│   ├── 06_sensitivity.py
│   └── utils/
│       ├── io.py
│       └── stats.py
├── tests/
│   └── contract/
│       ├── test_dataset_schema.py
│       ├── test_correlation_schema.py
│       ├── test_model_schema.py
│       └── test_results_schema.py
└── docs/
    └── paper_draft.md
```

## Phase & Task Mapping (covers every FR & SC)

| Phase | Task ID | Script | Primary Output | FR / SC addressed |
|-------|---------|--------|----------------|-------------------|
| **0 – Provenance Validation** | **T001** | `code/01_download_and_provenance.py` | `data/provenance/observed_checksums.json` | FR‑001, FR‑002, SC‑001 |
| **1 – Load Paired Dataset & Age Filter** | **T002** | `code/02_load_and_filter.py` | `data/processed/paired_dataset_age60.parquet` (if ≥ 200 rows) | FR‑001, SC‑001 |
| **1‑a – Size Abort** | **T002‑ABORT** | `code/02_load_and_filter.py` (post‑load) | Log entry; abort if rows < 200 | FR‑001 (implicit), SC‑001 |
| **2 – VIF Screening & Rarefaction** | **T003** | `code/02_load_and_filter.py` (VIF & rarefy) | Updated `paired_dataset_age60.parquet` (VIF‑flagged taxa removed) | FR‑010 |
| **3 – CLR Transformation, BMI Imputation & Post‑CLR Collinearity** | **T004** | `code/02_load_and_filter.py` | `clr_normalized.parquet`, `imputed.parquet` | FR‑002, FR‑010 (post‑CLR), FR‑009 |
| **4 – Covariate‑Adjusted Spearman + BH‑FDR** | **T005** | `code/03_correlation.py` | `data/results/correlations.json` | FR‑003, SC‑002 |
| **5 – Random Forest (Nested CV)** | **T006** | `code/04_modeling.py` | `data/results/model.json` | FR‑004, FR‑008 |
| **5‑a – Permutation Null Distribution** | **T007** | `code/04_modeling.py` (permutations) | Embedded in `model.json` | FR‑004, SC‑003 |
| **6 – Standard Linear Regression** | **T014** | `code/05_linear_regression.py` | `data/results/linear_regression.json` | FR‑013, SC‑002 |
| **7 – Rarefaction Depth Sensitivity Sweep** | **T009** | `code/06_sensitivity.py` | `data/results/sensitivity.json` | FR‑005 |
| **8 – Power Analyses (Correlation & Regression)** | **T010** | `code/06_sensitivity.py` (power module) | Power warnings in `summary.md` | FR‑009, SC‑004 |
| **9 – RAM Guardrail** | **T011** | `code/utils/stats.py` (monitor) invoked by all scripts | Runtime logs; automatic taxa truncation / permutation reduction if RAM > 6 GB | Internal safeguard (supports SC‑004) |
| **10 – Unified Results Assembly (Checksums Included)** | **T012** | `code/06_sensitivity.py` | `data/results/unified_results.json` | FR‑001, FR‑011, all FR/SC (implicit) |
| **11 – Reporting** | **T013** | `code/06_sensitivity.py` (summary generation) | `data/results/summary.md` | SC‑001 – SC‑004 |

All tasks are deterministic, produce real files, and are validated by the contract tests listed in `tests/contract/`. Downstream tasks (4‑11) are **conditionally executed** only when the paired dataset exists and meets the ≥ 200 participant threshold; otherwise the pipeline stops after T002‑ABORT and reports the fatal coverage gap, satisfying SC‑001 by explicitly documenting the failure rather than fabricating data.

---



