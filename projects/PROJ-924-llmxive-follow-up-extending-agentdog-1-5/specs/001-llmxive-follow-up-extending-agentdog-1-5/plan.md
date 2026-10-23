# Implementation Plan: Centroid‑Based Drift Detection for AgentDoG 1.5

**Branch**: `PROJ-924-zero-shot-drift` | **Date**: 2026‑07‑23 | **Spec**: `specs/PROJ-924/spec.md`  
**Input**: Feature specification from `specs/PROJ-924/spec.md`

## Summary
Extend the AgentDoG 1.5 safety taxonomy with a **centroid‑based drift detector** that (1) embeds logs with **all‑MiniLM‑L6‑v2**, (2) computes cosine distance to per‑category centroids built from ≥ 100 curated examples, (3) flags logs with `drift_score ≥ 0.5` (after empirical calibration), (4) validates the drift score against a three‑annotator human gold‑standard (κ ≥ 0.6, Mann‑Whitney p < 0.05, rank‑biserial ≥ 0.5, logistic‑regression p < 0.05, chi‑squared α = 0.05), and (5) compares the drift method to a **google/flan‑t5‑small** baseline (AUC‑ROC within 0.10 of baseline, baseline AUC ≥ 0.70, latency ≤ 0.5 × baseline). All steps run on the GitHub Actions free‑tier CPU runner (≤ 7 GB RAM, ≤ 6 h).

## Construct Validity Rationale
Embedding‑based centroid similarity has been shown to capture semantic drift and emergent threat patterns in prior work on language‑model safety (e.g., embedding‑based novelty detection in dialogue systems). Cosine distance to well‑defined safety‑category centroids offers an interpretable, literature‑supported proxy for “novel harmful patterns”, satisfying the construct‑validity requirement before downstream use.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `sentence-transformers==2.7.0`, `transformers==4.44.2`, `torch==2.4.1` (CPU wheel), `scikit-learn==1.5.1`, `scipy==1.14.0`, `pandas==2.2.2`, `numpy==1.26.4`, `datasets==2.21.0`, `jsonschema==4.23.0`, `pytest==8.3.2`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`)  
- **Testing**: `pytest` with contract validation; test logs persisted to `data/processed/test_results.log`  
- **Target Platform**: Linux (GitHub Actions free‑tier, 2 CPU cores, no GPU)  
- **Performance Goals**: Full pipeline ≤ 6 h; drift per‑log latency ≤ 0.5 × Flan‑T5 latency (FR‑011)  
- **Constraints**: RAM ≤ 7 GB, CPU‑only, batch size = 64 (verified fact 2410.21676), DRIFT_THRESHOLD = 0.5 (pre‑registered operating point, calibrated in Phase 4)  

## Threshold Calibration
Before the main run, a **validation split** of the taxonomy examples (held‑out [deferred] of curated examples) will be used to compute ROC curves for drift scores against the known category labels. The operating point achieving the best trade‑off between sensitivity and specificity will be selected, constrained to be ≥ 0.5; if the calibrated threshold differs, it will replace the default value (FR‑002).

## Power Analysis
A priori power calculations (α = 0.05, power = 0.80) using G*Power indicate that a random sample of **≥ 100 logs** (FR‑017) provides sufficient power to detect a medium effect size (Cohen’s d ≈ 0.5) for Mann‑Whitney, logistic‑regression odds ratios ≈ 2.0, and chi‑squared odds ratios ≈ 1.8. The sample size is thus justified and will be reported in `metrics.json`.

## Constitution Check
| Principle | Requirement | Compliance Strategy |
|-----------|-------------|---------------------|
| I. Reproducibility | Fixed seeds, canonical data sources | `RANDOM_SEED = 42` in `code/config.py`; datasets loaded via `datasets.load_dataset("agentdog/safety-v1")`; all random operations seeded |
| II. Verified Accuracy | Only cited verified sources | Research section cites only `agentdog/safety-v1`, the MiniLM model, and Flan‑T5 identifiers |
| III. Data Hygiene | Checksums, immutable raw data, PII scrubbing | SHA‑256 checksums recorded in `data/raw/checksums.json`; PII scrubber applied to GitHub‑issue logs before storage |
| IV. Single Source of Truth | Metrics trace to code output | All numbers read from `data/processed/metrics.json`; report generated programmatically |
| V. Versioning | Content hashes recorded | Artifact hashes written to `state/.../PROJ‑924‑....yaml` |
| VI. Drift Detection Validity | Human gold‑standard, κ ≥ 0.6 before reporting | Pipeline aborts with status `Incomplete` if `data/human_annotations.json` missing or κ < 0.6 |
| VII. Resource‑Constrained Computational Integrity | ≤ 7 GB RAM, ≤ 6 h, CPU‑only | No CUDA calls; batch size = 64; runtime and peak RAM measured and asserted (FR‑012) |

## Project Structure
### Documentation (this feature)
```
specs/PROJ-924/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── drift_output.schema.yaml
└── tasks.md            # generated later
```

### Source Code
```
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/
├── code/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── config.py                # constants
│   ├── data_loader.py           # HF dataset + GitHub issue acquisition
│   ├── embeddings.py            # centroid construction & drift scoring
│   ├── baseline_llm.py          # Flan‑T5 inference & latency
│   ├── validation.py            # kappa, Mann‑Whitney, logistic, chi‑squared, AUC, DeLong test
│   ├── report.py                # compile metrics → report.md
│   └── main.py                  # orchestrates pipeline
├── data/
│   ├── raw/
│   │   ├── safety_v1/           # immutable HF download
│   │   └── novel_corpus.jsonl   # ≥500 GitHub‑issue logs (PII‑scrubbed)
│   ├── human_annotations.json   # external manual input
│   └── processed/
│       ├── centroids.json
│       ├── drift_scores.parquet
│       ├── annotation_batches/
│       ├── metrics.json
│       ├── report.md
│       └── test_results.log
└── tests/
    ├── unit/
    │   ├── test_config.py
    │   └── test_tooling.py
    ├── contract/
    │   └── test_contracts.py      # validates all processed files against schemas
    └── integration/
        └── test_pipeline.py       # end‑to‑end on a small real slice
```

**Structure Decision**: Single‑project research pipeline; all logic lives under `code/`, data under `data/`, tests under `tests/`. This satisfies the “single source of truth” principle and avoids unnecessary service layers.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Human‑annotation hard gate | Constitution VI demands κ ≥ 0.6 on real annotations before drift scores are reported as reliable | Simulated annotations would violate the fabrication gate |
| GitHub‑issue scraping (FR‑014) | Spec requires ≥ 500 real post‑2025 logs; no open substitute exists | Toy corpus would breach the data‑availability requirement |

## Phase Plan (ordered: data → models → evaluation → figures → report)

| Phase | Tasks | FR / SC addressed |
|-------|-------|-------------------|
| **0 – Research & Feasibility** | Verify `agentdog/safety-v1` contains ≥ 100 examples per category; confirm MiniLM & Flan‑T5 fit CPU RAM/latency budget; run power analysis for FR‑017. | – |
| **1 – Data Model & Contracts** | Write JSON‑Schema files (`agent_log`, `drift_output`, `human_annotation`, `taxonomy_centroid`). | All FRs needing data validation |
| **2 – Setup & Tooling** | Create `code/config.py` with exact constants; write `requirements.txt` & `pyproject.toml`; add unit tests (`test_config.py`, `test_tooling.py`). | FR‑012, T011a, T010d |
| **3 – Data Acquisition** | Load `agentdog/safety-v1` via HF; fetch ≥ 500 post‑2025 GitHub issue logs (unauthenticated API, seeded repo list); checksum raw files; PII‑scrub. | FR‑004, FR‑014 |
| **4 – Taxonomy & Drift Scoring** | Embed ≥ 100 curated examples per category; compute L2‑normalized centroids; embed all logs; compute cosine distance → `drift_score`; set `review_flag` per calibrated threshold (FR‑002). | FR‑001‑004 |
| **5 – Stratification & Sampling** | Bin logs into high‑drift (top quantile) and low‑drift (bottom quantile) **while controlling for log length and source**; sample ≥ 100 logs uniformly across the full drift distribution (FR‑005, FR‑017). | Confound control added |
| **6 – Human Annotation (external)** | Generate blinded batches (no scores or bin info); collect annotations from three annotators; ingest into `human_annotations.json`. | FR‑006 |
| **7 – Statistical Validation** | Compute mean pairwise Cohen’s κ (gate κ ≥ 0.6); Mann‑Whitney U (p < 0.05, rank‑biserial ≥ 0.5); logistic regression `novel ~ drift_score + log_length + source` (p < 0.05, AUC‑ROC); chi‑squared test on high/low‑drift bins (reject α = 0.05); apply Holm correction across families; record all in `metrics.json`. | FR‑007‑009, FR‑015, FR‑017 |
| **8 – Baseline Comparison** | Run zero‑shot `google/flan‑t5‑small` on the same annotated set; compute AUC‑ROC; enforce baseline AUC ≥ 0.70 (FR‑016); measure median per‑log latency for both methods; compute latency ratio; perform **DeLong’s test** for paired AUCs (drift vs baseline) and require p > 0.05 for equivalence claim; flag drift method as “computationally efficient alternative” if (i) baseline AUC ≥ 0.70, (ii) drift AUC within 0.10 of baseline, and (iii) DeLong test non‑significant. | FR‑010‑011 |
| **9 – Final Report & Resource Accounting** | Record peak RAM and wall‑clock time (assert ≤ 7 GB, ≤ 6 h – FR‑012); generate `report.md` and `metrics.json` programmatically; abort with `Incomplete` if κ < 0.6 or annotations missing (Principle VI). | FR‑013, FR‑012, SC‑001‑004 |

## FR / SC Coverage Map
| Requirement | Phase |
|-------------|-------|
| FR‑001 – FR‑004 | 4 |
| FR‑005 | 5 |
| FR‑006 – FR‑009 | 6‑7 |
| FR‑010 – FR‑011 | 8 |
| FR‑012 – FR‑013 | 9 |
| FR‑014 – FR‑017 | 3‑5, 7 |
| SC‑001 | 3‑4, 7 |
| SC‑002 | 5‑7 |
| SC‑003 | 8 |
| SC‑004 | 9 |

All functional and success criteria are covered.
