# Implementation Plan: Evaluating the Statistical Validity of Common Ranking Metrics

**Branch**: `001-statistical-validity-ranking-metrics` | **Date**: 2023-10-27 | **Spec**: `specs/001-statistical-validity-ranking-metrics/spec.md`
**Input**: Feature specification from `/specs/001-statistical-validity-ranking-metrics/spec.md`

## Summary

This project implements a rigorous statistical validation framework for common Information RetrieVAL (IR) ranking metrics (NDCG@10, MAP) using TREC benchmark data. The core approach involves generating null distributions via permutation tests (shuffling relevance labels), calculating permutation p-values, performing bootstrap-based power analysis to determine Minimum Detectable Effect Size (MDES), and applying Benjamini-Hochberg correction for multiple comparisons. The system is designed to run entirely on CPU within GitHub Actions free-tier constraints (limited cores, constrained RAM, bounded execution time)., utilizing `ir-datasets` for verified data access and `scipy`/`numpy` for statistical computations.

**Key Clarification**: The analysis validates the *discriminative power* of the metrics (i.e., their ability to distinguish a relevant ranking from a random permutation of labels) and characterizes the null distribution of scores. It does not claim to test the theoretical "statistical validity" (error rates) of the metrics in isolation, but rather provides empirical evidence of their sensitivity to the signal in the data.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `ir-datasets`, `numpy`, `pandas`, `scipy`, `tqdm`  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` (unit tests for metric calculation, permutation logic; integration tests for full workflow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI / Research Script  
**Performance Goals**: ≤ 6 hours runtime, ≤ 7 GB peak RAM, deterministic results via pinned seeds  
**Constraints**: CPU-only execution; no external API keys; strict data hygiene (checksums, immutable raw data)  
**Scale/Scope**: TREC Robust 2004 and Web Track 2009-2012 datasets. Up to 500 queries processed (subsampled if necessary).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: ✅ Pinned seeds in code; `ir-datasets` ensures canonical source; `requirements.txt` pins dependencies.
- **II. Verified Accuracy**: ✅ All external citations (TREC, statistical methods) verified against primary sources or standard references.
- **III. Data Hygiene**: ✅ Raw data checksummed; no in-place modifications; derivations written to new files; PII scan passed (TREC qrels are anonymous). Subsample logs recorded in `data/processed/subsample_log.csv`.
- **IV. Single Source of Truth**: ✅ All statistics trace to `data/processed` CSVs; code in `code/` generates figures/tables.
- **V. Versioning Discipline**: ✅ Artifact hashes recorded in `state/` YAML; content hashes used for invalidation.
- **VI. Statistical Power Transparency**: ✅ MDES and power estimates included in all results; effect sizes reported with scores in all tables/figures.
- **VII. Benchmark Integrity**: ✅ Only official TREC collections used; subsampling logged explicitly in `data/processed/subsample_log.csv` with trigger reasons.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-validity-ranking-metrics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── qrels.schema.yaml
│   ├── null_distribution.schema.yaml
│   ├── results.schema.yaml
│   ├── results_summary.schema.yaml
│   ├── alpha_sweep.schema.yaml
│   └── subsample.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── data_loader.py       # ir-datasets wrapper (adheres to contracts/qrels.schema.yaml)
├── metrics.py           # NDCG@10, MAP, IDCG
├── permutation.py       # Null distribution generation (adheres to contracts/null_distribution.schema.yaml)
├── inference.py         # P-values, BH correction, MDES (adheres to contracts/results.schema.yaml)
├── sensitivity.py       # Alpha sweep analysis (adheres to contracts/alpha_sweep.schema.yaml)
├── reporting.py         # CSV/PNG generation (adheres to contracts/results_summary.schema.yaml)
└── main.py              # Orchestration

data/
├── raw/                 # Downloaded TREC qrels (immutable)
│   ├── trec-robust-04.qrels
│   └── trec-web-2009.qrels (etc.)
└── processed/           # Derived datasets
    ├── query_metrics.csv
    └── subsample_log.csv  # Records dropped queries per FR-011

results/
├── null_distributions/  # Per-query null score tables (adheres to contracts/null_distribution.schema.yaml)
├── alpha_sweep.csv      # Sensitivity analysis (adheres to contracts/alpha_sweep.schema.yaml)
├── results_summary.csv  # Final summary (adheres to contracts/results_summary.schema.yaml)
└── plots/               # Density plots
```

**Structure Decision**: Single project structure selected to minimize overhead for a research script. All logic is modularized into distinct modules for testability. Data is separated into raw (immutable) and processed (derived) to satisfy Constitution Principle III. Subsample logs ensure traceability for FR-011.

## Complexity Tracking

| Constraint-Driven Design Decision | Why Needed | Simpler Alternative Rejected Because |
|-----------------------------------|------------|-------------------------------------|
| Subsampling logic (FR-011) | Required to meet 6-hour runtime on full TREC Web Track. | Running full Web Track on a limited number of cores would exceed 6 hours.; subsampling is the only honest path to CI completion. |
| BH Correction (FR-005) | Required for multiple hypothesis testing across queries. | Bonferroni is too conservative for exploratory IR studies; BH maintains power while controlling FDR. |
| MDES via Bootstrap (FR-006) | Required to quantify statistical power. | Analytical power calculations are intractable for complex ranking metrics; bootstrap is the standard empirical approach. |
