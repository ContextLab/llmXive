# Implementation Plan: Video Reasoning Threshold Analysis

**Branch**: `001-video-reasoning-threshold` | **Date**: 2026-10-25 | **Spec**: `specs/001-llmxive-follow-up-extending-videokr-towa/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-videokr-towa/spec.md`

## Summary
The pipeline will (1) **download the official VideoKR‑SFT dataset** and its accompanying **ground‑truth knowledge graph** (both required by the specification) – if either is missing the pipeline aborts with a clear error; (2) annotate each question with the shortest‑path hop count (`chain_length`) derived **solely** from this KG, ensuring structural annotation integrity (Constitution VI); (3) perform a **power analysis** to guarantee ≥ 100 samples per hop‑bin (effect size = 0.1, 80 % power, α = 0.05); (4) stratify accuracy by hop‑bin, flagging any bin that fails the power requirement; (5) detect a “reasoning cliff” **associatively** using both a **covariate‑adjusted permutation change‑point test** (10,000 permutations) and a **logistic‑regression likelihood‑ratio test (LRT)** across candidate knots = {1,2,3,4,5} with Bonferroni correction; (6) repeat detection under three explicit binning schemes (S1 = `'1','2','3+'`, S2 = `'1','2','3','4+'`, S3 = `'1','2','3','4','5+'`); (7) train a **text‑only logistic regression** baseline and an **extended model** that adds `chain_length`; (8) evaluate the added predictor with an LRT and a covariate‑adjusted LRT, injecting the predicted probability into `predicted_correctness`; (9) log total runtime and peak memory usage, comparing them against CI limits; (10) produce all required JSON/CSV/PNG artifacts **as the single source of truth** for each statistic; (11) **global random‑seed pinning** for all stochastic steps (`SEED = 42` in `utils/config.py`); (12) ensure the entire workflow runs within the GitHub Actions free‑tier limits (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h). No synthetic data are created; only real, publicly downloadable data drive the analysis.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `pandas`, `numpy`, `networkx`, `scipy`, `statsmodels`, `scikit-learn`, `pyyaml`, `datasets` (HuggingFace), `tqdm`  
- **Storage**: Local filesystem under `data/` (raw & processed)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions free‑tier runner  
- **Project Type**: Research‑pipeline library (CLI‑driven)  
- **Performance Goals**: End‑to‑end runtime ≤ 7200 s, peak RAM ≤ 7 GB  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | Full – all steps scripted, **global seed `SEED=42`** pinned, data fetched from canonical public sources. |
| II. Verified Accuracy | No external citations beyond open datasets; URLs verified where available. |
| III. Data Hygiene | Raw VideoKR‑SFT files checksummed; transformations produce new files. |
| IV. Single Source of Truth | **Explicitly stated**: each generated artifact is the sole source for its corresponding statistic. |
| V. Versioning Discipline | Content hashes recorded via `code/utils/versioning.py`. |
| VI. Structural Annotation Integrity | Hop counts derived **only** from the ground‑truth KG, independent of model predictions. |
| VII. Threshold Sensitivity Analysis | Both permutation test and LRT performed; sensitivity sweep over three binning schemes included. |

## Project Structure
```text
specs/001-video-reasoning-threshold/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── annotated_questions.schema.yaml

code/
├── ingest/
│   ├── download_videokr.py          # fetches VideoKR‑SFT; aborts if unavailable
│   ├── download_kg.py               # fetches ground‑truth KG; aborts if unavailable
│   ├── annotate_graph.py
│   └── checksum.py
├── analysis/
│   ├── power_analysis.py
│   ├── stratify_accuracy.py
│   ├── detect_threshold.py
│   ├── sensitivity.py
│   ├── model_lrt.py
│   └── diagnostics.py
├── utils/
│   ├── entity_linker.py
│   ├── graph_utils.py
│   ├── config.py   # contains `SEED = 42`
│   ├── memory_tracker.py
│   └── versioning.py
└── main.py

tests/
├── unit/
│   ├── test_entity_linker.py
│   └── test_memory_tracker.py
└── integration/
    └── test_pipeline.py

data/
├── raw/
│   ├── videokr_sft/          # VideoKR‑SFT files (downloaded)
│   └── kg/                   # Ground‑truth knowledge graph files
└── processed/
    ├── annotated_videokr.csv
    ├── chain_bins.csv
    ├── accuracy_binned.png
    ├── accuracy_binned.csv
    ├── accuracy_vs_hop_raw.png
    ├── accuracy_vs_hop_raw.csv
    ├── threshold_results.json
    ├── sensitivity_analysis.json
    ├── model_lrt_results.json
    ├── confound_adjusted_lrt.json
    ├── power_analysis.json
    ├── runtime_log.json
    ├── memory_log.json
    └── annotation_coverage.json
```

## Mapping of FR/SC to Plan Steps (including Data‑Model entities)
| ID | Requirement | Script / Phase | Output | Data‑Model Entity |
|----|-------------|----------------|--------|-------------------|
| FR-001 | Data Annotation | `code/ingest/annotate_graph.py` | `data/processed/annotated_videokr.csv` | **QuestionRecord** |
| FR-002 | Binning Strategy | `annotate_graph.py` | `data/processed/chain_bins.csv` | **QuestionRecord** |
| FR-003 | Stratified Accuracy | `code/analysis/stratify_accuracy.py` | `accuracy_binned.png`, `accuracy_binned.csv` | **QuestionRecord** |
| FR-004 | Threshold Detection (Permutation & LRT) | `code/analysis/detect_threshold.py` | `threshold_results.json` | **ThresholdResult** |
| FR-005 | Continuous Visualization | `detect_threshold.py` | `accuracy_vs_hop_raw.png`, `accuracy_vs_hop_raw.csv` | **QuestionRecord** |
| FR-006 | Runtime Measurement | `code/main.py` | `runtime_log.json` | — |
| FR-008 | Sensitivity Analysis | `code/analysis/sensitivity.py` | `sensitivity_analysis.json` | **ThresholdResult** |
| FR-009 | Memory Usage Logging | `code/utils/memory_tracker.py` | `memory_log.json` | — |
| FR-010 | Predictive Model & LRT | `code/analysis/model_lrt.py` | `model_lrt_results.json` | **QuestionRecord** |
| FR-011 | Power Analysis | `code/analysis/power_analysis.py` | `power_analysis.json` | — |
| FR-012 | Covariate Extraction | `annotate_graph.py` (adds columns) | `annotated_videokr.csv` | **QuestionRecord** |
| FR-013 | Predicted Correctness Injection | `model_lrt.py` (post‑training) | `annotated_videokr.csv` (updated) | **QuestionRecord** |
| FR-014 | Ingestion Script Success | `download_videokr.py` & `download_kg.py` log exit codes | `ingest_log.json` | — |
| SC-001 | Annotation Coverage | `annotate_graph.py` | `annotation_coverage.json` | — |
| SC-002 | Threshold Significance | `detect_threshold.py` | `threshold_results.json` (`is_significant`) | **ThresholdResult** |
| SC-003 | Robustness Verification | `sensitivity.py` | `sensitivity_analysis.json` (`robustness_status`) | **ThresholdResult** |
| SC-004 | Runtime Compliance | `runtime_log.json` | `runtime_log.json` | — |
| SC-005 | Memory Compliance | `memory_log.json` | `memory_log.json` | — |
| SC-006 | Extended Confound Robustness | `model_lrt.py` (covariate‑adjusted) | `confound_adjusted_lrt.json` | **ThresholdResult** |
| SC-007 | Model LRT Evaluation | `model_lrt.py` | `model_lrt_results.json` | **QuestionRecord** |
| SC-008 | Predicted Correctness Column Validation | `model_lrt.py` validation step | `predicted_correctness_check.json` | **QuestionRecord** |
| SC-009 | Ingestion Script Success | `download_*` scripts log exit codes | `ingest_log.json` | — |
| SC-010 | Real Dataset Usage | Checksums of VideoKR‑SFT files | `dataset_verification.json` | — |
| SC-011 | Correctness Label Integrity | Verification step | `label_integrity_check.json` | — |

## Computational Feasibility
- **CPU‑first**: All libraries run on the CI runner.  
- **Memory**: VideoKR‑SFT (~800 MB) + trimmed KG (< 1 GB) → peak < 2 GB.  
- **Runtime**: Estimated ≤ 1.5 h (including 10,000 permutations). Meets CI limit of 7200 s.

## Risk Management
| Risk | Mitigation |
|------|------------|
| Required datasets unavailable | Abort with clear error; no TVQA/ConceptNet fallback. |
| Entity linking precision | `entity_linker.py` uses exact match + Levenshtein ≤ 2; validation set required ≥ 95 % accuracy. |
| Insufficient high‑hop samples | Power analysis guarantees ≥ 100 per bin; bins still lacking are merged and flagged. |
| Out‑of‑memory on large graph | KG trimmed to entities appearing in VideoKR‑SFT; streaming fallback available. |
| Permutation test exceeds CI time | `NUM_PERMUTATIONS = 10000` is balanced for CI runtime; configurable if needed. |
| Download failure | Robust download scripts abort with clear logs; CI surfaces the failure. |

## Seed Pinning (Constitution I)
All stochastic components (permutation test, model training, CV splits) use the globally defined seed `SEED = 42` from `utils/config.py`. This ensures exact reproducibility across CI runs.

## Single Source of Truth (Constitution IV)
Each generated artifact (figures, CSVs, JSONs) is declared the **sole source** for its corresponding statistic. No hand‑typed numbers appear elsewhere in the repository, satisfying the single‑source‑of‑truth requirement.
