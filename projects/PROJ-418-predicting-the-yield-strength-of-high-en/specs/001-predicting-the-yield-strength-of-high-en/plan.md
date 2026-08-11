# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `feature/hea-yield-prediction` | **Date**: 2026‑08‑11 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/feature/hea-yield-prediction/spec.md`

## Summary
Develop an end‑to‑end CPU‑first pipeline that (1) downloads a curated, open‑source HEA yield‑strength dataset (OpenML ID 4539), (2) validates records against JSON schemas, (3) computes composition‑based descriptors with literature‑backed justification, (4) trains a Random Forest regressor using a fixed 80/20 train‑test split and 5‑fold CV on the training portion, (5) evaluates on the held‑out test set, (6) computes permutation importance with exactly **1 000 permutations** per feature **on the held‑out test set** and assesses significance via a two‑tailed t‑test (normality check included) with Bonferroni correction, (7) records reproducibility metadata (seeds, hyperparameters, software versions, timestamps, checksums, and traceability IDs), (8) generates a markdown `report.md` that includes dataset statistics, model performance, importance rankings, VIF analysis, and the reproducibility manifest, and (9) enforces linting and formatting checks. All functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑008) are explicitly addressed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit‑learn==1.5.*`, `scipy==1.13.*`, `joblib==1.4.*`, `jsonschema==4.22.*`, `matplotlib==3.9.*`, `seaborn==0.13.*`, `ruff==0.6.*`, `black==24.4.*`  
- **Storage**: Files under `data/` (raw, processed) and `output/` (models, reports, runtime logs)  
- **Testing**: `pytest==8.2.*` with contract‑validation tests  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ~14 GB disk)  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 2 h on an 8‑core CPU (SC‑004)  
- **Constraints**: Fixed permutation count = 1 000 (FR‑012); no adaptive counts.

## Constitution Check
| Principle | Reference | How the plan satisfies it |
|-----------|-----------|---------------------------|
| I. Reproducibility | Core Principle I | All random seeds are pinned; `requirements.txt` pins exact library versions; dataset fetched from the canonical OpenML URL on every run; `manifest.json` records timestamps, software versions, and checksums. |
| II. Verified Accuracy | Core Principle II | External citations (e.g., Zhang et al., 2015) are verified; title‑token overlap ≥ 0.7. |
| III. Data Hygiene | Core Principle III | Raw dataset checksum recorded; every transformation writes a new file with documented checksum; no PII. |
| IV. Single Source of Truth | Core Principle IV | Every figure/table in `report.md` includes a deterministic identifier (`ID: <sha256>`) linking back to a single data row and the exact code block; these mappings are stored in `manifest.json` (`traceability` map). |
| V. Versioning Discipline | Core Principle V | Content hashes recorded in `manifest.json`; any artifact change updates the project state timestamp. |
| VI. Deterministic Descriptor Engineering | Domain‑specific Principle VI | Descriptor functions live in `src/descriptors/` and use a single elemental property table (`data/elemental_properties.csv`). |
| VII. Statistical Rigor and Uncertainty Quantification | Domain‑specific Principle VII | 5‑fold CV, bootstrap CI (≥ 1 000 resamples, deferred), permutation importance with 1 000 permutations, Bonferroni correction, VIF calculation, full logging of seeds. |

## Project Structure
```
src/
├── pipeline/
│   ├── __init__.py
│   ├── data.py            # download, checksum, validation (FR‑001, FR‑013, FR‑009)
│   ├── descriptors.py     # deterministic descriptor computation (FR‑002, VI)
│   ├── model.py           # RF training, CV, prediction (FR‑003, VII)
│   ├── importance.py      # permutation importance + t‑test + Bonferroni (FR‑005, FR‑006, FR‑012)
│   ├── report.py          # markdown generation with traceability IDs (FR‑008, IV)
│   └── manifest.py        # manifest creation (FR‑007, I)
├── contracts/
│   ├── dataset.schema.yaml
│   ├── elemental_properties.schema.yaml
│   ├── hea_composition.schema.yaml
│   ├── descriptor.schema.yaml
│   ├── importance.schema.yaml
│   ├── performance.schema.yaml
│   ├── runtime.schema.yaml
│   └── manifest.schema.yaml
tests/
├── contract/
│   └── test_schemas.py    # validates all artifacts against contracts (FR‑013)
└── integration/
    └── test_end_to_end.py # runs full pipeline, checks SC‑001‑SC‑008
data/
├── raw/
│   └── hea_yield_strength.jsonl   # downloaded via OpenML ID 4539
├── processed/
│   └── descriptors.parquet
└── elemental_properties.csv
output/
├── model/
│   └── random_forest.joblib
├── report/
│   └── report.md
├── manifest/
│   └── manifest.json
├── metrics/
│   ├── performance.json
│   ├── importance.json
│   └── runtime.json
└── stability/
    └── top5_rankings.json
scripts/
└── run_pipeline.py
requirements.txt
README.md
```

## Phase Mapping (FR/SC → Plan Steps)

| Phase | Tasks | FR/SC Covered |
|-------|-------|---------------|
| **Phase 0 – Research & Data Acquisition** | Verify dataset availability (OpenML ID 4539), download, checksum, schema validation against `dataset.schema.yaml`, `elemental_properties.schema.yaml`, and `hea_composition.schema.yaml`; enforce FR‑009 abort on missing fields or duplicate rows (deduplicate). | FR‑001, FR‑013, FR‑009, SC‑005 |
| **Phase 1 – Descriptor Engineering** | Compute deterministic descriptors (mixing entropy, atomic size mismatch, electronegativity variance, VEC, melting‑temperature variance) using the single elemental property table; validate output against `descriptor.schema.yaml`. Literature justification (Zhang et al., 2015) provided. | FR‑002, VI, SC‑006 |
| **Phase 2 – Model Training** | Fixed **[deferred] train / [deferred] test** split (random_state = seed). Perform 5‑fold CV **only on the training portion**; train Random Forest (`n_estimators=500`, `max_depth=None`); record seeds, hyper‑parameters; store model artifact. | FR‑003, VII, SC‑001, SC‑002 |
| **Phase 3 – Evaluation** | Evaluate on the **held‑out test set**: compute R², Pearson r, two‑tailed p‑value; bootstrap 1 000 resamples for 95 % CI; perform a concrete power analysis (Cohen f² = 1.5, N≈1200 → > 80 % power). | FR‑004, SC‑001, SC‑002, SC‑003 |
| **Phase 4 – Permutation Importance** | Compute importance with exactly **1 000 permutations** per feature **on the held‑out test set**; obtain empirical mean/std; assess significance with a **two‑tailed t‑test** (normality checked via Shapiro‑Wilk; if violated, flag limitation); apply Bonferroni correction; output conforms to `importance.schema.yaml`. | FR‑005, FR‑006, FR‑012, SC‑003 |
| **Phase 5 – Reporting & Manifest** | Generate `report.md` (includes dataset stats, model performance, VIF analysis, importance rankings with traceability IDs); create `manifest.json` (records seeds, hyper‑parameters, software versions, timestamps, SHA‑256 checksums, and `traceability` map linking each figure/table to source row & code hash); validate all derived artifacts (`descriptors.parquet`, `performance.json`, `importance.json`, `runtime.json`) against their contracts. | FR‑007, FR‑008, FR‑011, SC‑004, SC‑006, SC‑007, SC‑008 |
| **Phase 6 – Quality Assurance** | Lint (`ruff` ≤ 5 warnings, output saved to `logs/ruff.log`), format (`black --check`); validate `runtime.json` against `runtime.schema.yaml` (enum check). | FR‑011, SC‑008, contract compliance |

## Compute Feasibility
- **CPU‑first**: All steps use scikit‑learn, NumPy, and joblib; they run comfortably on the free GitHub Actions runner.  
- **Memory**: Descriptor table (~1 200 × ~30 features) < 200 MB. Random Forest with 500 trees < 1 GB.  
- **Runtime Budget**: Estimated brief time for descriptor computation, 30 min for RF training + CV, 45 min for permutation importance (parallelized across 8 cores), 5 min for reporting, 5 min for validation → total ≈ on the order of an hour, satisfying SC‑004.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Dataset not open | Primary source is OpenML ID 4539, which is programmatically downloadable without credentials. |
| Permutation importance runtime | Parallelize across features (`n_jobs=-1`); if runtime exceeds 2 h, sample 5 000 rows (random seed fixed) and note the limitation. |
| Multiple‑comparison inflation | Use Bonferroni correction on t‑test p‑values; report both raw and corrected values. |
| Collinearity | Compute VIF for each descriptor; if VIF > 5, flag and optionally drop the descriptor (documented in report). |
| Power justification | Provide concrete Cohen’s f² calculation and reference to Cohen (1988). |
| Normality assumption for t‑test | Perform Shapiro‑Wilk test; if violated, report p‑values as approximate and discuss limitation. |

## Traceability Enforcement (Principle IV)
Each figure/table in `report.md` will contain a caption of the form `ID: <sha256>` where the hash is computed from the concatenation of the source data row (as JSON) and the exact code block that produced the statistic. `manifest.json` includes a `traceability` map:

```json
{
  "figure_1": {"source_row_id": "HEA_042", "code_hash": "a1b2c3..."},
  "table_3": {"source_row_id": "HEA_017", "code_hash": "d4e5f6..."}
}
```

This satisfies Principle IV by providing a single source of truth for every reported number.

--- 

## projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/research.md
# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
This document records the research decisions that shape the implementation plan. All cited resources are drawn from the verified dataset list provided by the project owner.

## Dataset Strategy

| Role | Source | Loader | Verification |
|------|--------|--------|--------------|
| **Primary Yield‑Strength Dataset** | OpenML dataset ID `4539` (“HEA_Composition_Yield”) – an openly accessible collection of experimentally measured yield strengths for a large set of single‑phase HEAs. | `openml.datasets.get_dataset(4539)` | Verified reachable via OpenML API (checksum recorded). |
| **Elemental Property Table** | `https://huggingface.co/datasets/materials/elemental_properties/resolve/main/elemental_properties.csv` | `datasets.load_dataset("materials/elemental_properties")` | Verified reachable CSV (checksum recorded). |
| **Verification Datasets (for sanity checks)** | *None required* | – | – |

> **Note**: The previously mentioned curated dataset (‑020‑00374‑5) is not publicly downloadable and therefore is **not** used in the pipeline; the OpenML dataset fulfills all FR‑001 requirements.

## Methodology Rationale

| Step | Chosen Method | CPU/GPU | Reasoning |
|------|---------------|---------|-----------|
| **Descriptor Calculation** | Vectorized NumPy/Pandas functions (atomic radius variance, electronegativity variance, mixing entropy, VEC, melting‑temperature variance). These descriptors are standard in HEA literature (e.g., Zhang *et al.*, *Acta Materialia* 2015, DOI:10.1016/j.actamat.2015.04.028). | CPU | Deterministic, low‑memory, fully reproducible. |
| **Model** | Random Forest Regressor (`n_estimators=500`, `max_depth=None`). | CPU | Handles non‑linear interactions, robust to collinearity, fast training on modest data. |
| **Cross‑Validation & Data Split** | Fixed **[deferred] train / [deferred] test** split (random_state = seed) performed **before** any cross‑validation. 5‑fold CV is performed **only on the training portion**. | CPU | Guarantees that the test set is completely disjoint from CV folds, preventing leakage. |
| **Performance Evaluation** | Compute R², Pearson r, and two‑tailed p‑value on the held‑out test set; bootstrap 1 000 resamples for 95 % confidence intervals. | CPU | Provides unbiased performance estimate and uncertainty quantification. |
| **Power Analysis** | Effect size f² = R²/(1‑R²) = 1.5 (large). Using α = 0.05, N ≈ 1 200 yields > 80 % power to detect R² ≥ 0.6 (Cohen, *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., 1988). | CPU | Justifies that the dataset size is sufficient for the target performance. |
| **Permutation Importance** | `sklearn.inspection.permutation_importance` with **exactly 1 000 permutations** per feature **evaluated on the held‑out test set**; significance assessed with a **two‑tailed t‑test** (normality checked via Shapiro‑Wilk; if violated, limitation noted); Bonferroni correction for multiple comparisons. | CPU | Meets FR‑012, satisfies FR‑006, and provides rigorous significance testing. |
| **Statistical Rigor** | VIF calculated for each descriptor; VIF > 5 flagged in the report. All significance claims are associational; no causal inference is made. | CPU | Addresses Principle VII and ensures transparent reporting. |
| **Reproducibility** | All random seeds, hyper‑parameters, software versions, and timestamps are recorded in `manifest.json`. Inline code comments and a comprehensive `README.md` are provided (FR‑011). | CPU | Satisfies Constitution Principle I and FR‑011. |

## Decision / Rationale Summary
- **CPU‑first** for all steps; no GPU needed.  
- **OpenML fallback** ensures data availability on CI runners.  
- Fixed permutation count respects FR‑012.  
- All FR/SC IDs are explicitly mapped to plan phases (see `plan.md`).  

--- 
