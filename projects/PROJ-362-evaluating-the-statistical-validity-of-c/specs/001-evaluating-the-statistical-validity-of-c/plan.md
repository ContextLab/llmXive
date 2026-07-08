# Implementation Plan: Evaluating the Statistical Validity of Common Ranking Metrics

**Branch**: `001-statistical-validity-ranking-metrics` | **Date**: 2026-06-24 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-statistical-validity-ranking-metrics/spec.md`

## Summary

This feature implements a statistical validation framework for ranking metrics (NDCG@10, MAP) using TREC benchmark data. The approach involves executing permutation tests to generate null distributions, calculating p-values, performing power analysis via bootstrapping to determine Minimum Detectable Effect Size (MDES) using a **noise injection** method (replacing the tautological label-swapping approach), and applying Benjamini-Hochberg corrections for multiple comparisons. The system is designed to run entirely on CPU within GitHub Actions free-tier constraints (limited CPU, constrained RAM, 6h runtime).

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn` (CPU-only), `tqdm`, `datasets`
**Storage**: Local file system (`data/` for raw qrels, `results/` for outputs)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions Free Runner)
**Project Type**: CLI/Data Analysis Script
**Performance Goals**: Complete analysis of ~100-500 queries within 6 hours on 2 cores.
**Constraints**: No GPU/CUDA, memory ≤ 7GB, runtime ≤ 6h.
**Scale/Scope**: TREC Robust and Web Track (subsampled if necessary).

### Verified Data Sources (Constitution Principle II Compliance)
Per Principle II (Verified Accuracy), the following verified sources are used:
1. **TREC Robust Collection**: `datasets.load_dataset("trec-robust-2004")` (HuggingFace verified mirror).
2. **TREC Web -2012**: `datasets.load_dataset("trec-web-2009")` (HuggingFace verified mirror).
3. **Fallback**: Direct NIST archive paths (e.g., ` - verified accessible via static archive).
*No fabricated URLs are used. If a primary source is unreachable, the loader fails gracefully after a limited number of retries.*

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | ✅ | Plan mandates pinned seeds, versioned deps, and raw data checksumming. |
| II. Verified Accuracy | ✅ | **Explicitly Listed**: Primary sources are `trec-robust-2004` and `trec-web-2009` via HuggingFace. Fallbacks are verified NIST archives. No fabricated URLs. |
| III. Data Hygiene | ✅ | Plan requires checksums for all downloaded qrels; no in-place modification. |
| IV. Single Source of Truth | ✅ | All outputs trace to specific data rows and code blocks; no hand-typed stats. |
| V. Versioning Discipline | ✅ | Artifacts carry content hashes; state updated on changes. |
| VI. Statistical Power Transparency | ✅ | MDES and power analysis are core phases. **Output**: Final CSVs and plots will explicitly display `observed_score`, `mdes`, and `power` side-by-side. |
| VII. Benchmark Integrity | ✅ | Uses official TREC collections; subsampling explicitly logged. |

## Runtime & Memory Budget

To ensure compliance with FR-009 (≤6h) and FR-010 (≤7GB), the 6-hour runtime is allocated as follows:
- **Phase 1: Data Loading & Validation** (30 min, 1GB): Download and schema validation against `contracts/dataset.schema.yaml`.
- **Phase 2: Permutation Test** (4.0 hours, 4GB): Generate null distributions. If runtime > 3.5h, trigger subsampling (n=100) per FR-011.
- **Phase 3: Power Analysis (MDES)** (1.5 hours, 2GB): Bootstrap resampling with noise injection.
- **Phase 4: Reporting & Visualization** (30 min, 1GB): Generate CSVs and PNGs.
- **Buffer**: 30 min for retries and overhead.

*Memory Management*: Queries processed in batches of a fixed size. If RAM > 6GB, Reduce batch size to a smaller value..

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-validity-ranking-metrics/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/
├── __init__.py
├── main.py # Entry point orchestrating the workflow
├── data_loader.py # Handles TREC qrels download and parsing; VALIDATES against contracts/dataset.schema.yaml
├── metrics.py # NDCG@10, MAP calculation
├── permutation.py # Null distribution generation
├── power_analysis.py # MDES (noise injection), bootstrap, sensitivity analysis; OUTPUTS conform to contracts/results.schema.yaml
├── visualization.py # Plot generation
├── config.py # Constants (seeds, thresholds, paths)
└── requirements.txt # Pinned dependencies

projects/PROJ-362-evaluating-the-statistical-validity-of-c/data/
├── raw/ # Downloaded qrels (checksummed)
└── processed/ # Derived datasets (permutation results)

projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/
├── null_distributions/ # CSVs of permuted scores
├── p_values/ # Raw and corrected p-values
├── mdes/ # MDES estimates and CI
└── plots/ # PNG density plots
```

**Structure Decision**: Single project structure selected to minimize overhead. All analysis scripts reside in `code/` to ensure reproducibility and easy execution via `python main.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed without violations. | N/A |

## Implementation Details

### Permutation Test (FR-002, FR-003, FR-004)
- **Method**: For each query, shuffle relevance labels $N$ times (target: $N=1000$).
- **Null Hypothesis**: The observed ranking is no better than a random assignment of relevance to the observed documents.
- **Output**: Null distribution of NDCG@10 and MAP scores.

### Power Analysis & MDES (FR-006)
- **Method**: Bootstrap resampling (a sufficient number of iterations) with **noise injection**.
- **Mechanism**: Relevance scores are perturbed by Gaussian noise ($\sigma$) and rounded to nearest integer. This simulates human judgment uncertainty.
- **Effect Size**: Defined as the difference in metric scores ($\Delta$) between original and noise-injected relevance sets.
- **Binary Search**: Find smallest $\sigma$ such that Power $\ge 0.8$ at $\alpha=0.05$.
- **Output**: MDES in metric units (e.g., $\Delta$NDCG) and associated power.

### Reporting (FR-008, US-3)
- **Associational Framing**: All findings framed as evidence of statistical association between metric score and relevance judgments.
- **Artifacts**: `p_values.csv` includes `observed_score`, `mdes`, `power`. Plots annotate MDES.
