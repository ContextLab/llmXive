# Implementation Plan: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

**Branch**: `001-llmxive-prp-redundancy` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-prp-redundancy/spec.md`

## Summary

This feature validates the hypothesis that semantic redundancy in retrieval lists degrades the efficiency of Active Pairwise Ranking Prompting (PRP) rankers by wasting LLM call budgets on near-duplicate comparisons. The plan implements a CPU-tractable pipeline that: (1) synthetically injects redundancy into BEIR datasets (`scifact`, `nfcorpus`), (2) measures "wasted" calls via a cosine-similarity proxy (definitive for operational loop, validated via stratified sampling from all calls), (3) applies MinHash-LSH pre-clustering to filter redundant pairs, and (4) statistically validates the recovery of NDCG@10 and call efficiency. The entire pipeline is constrained to run within 6 hours and 7GB RAM on a GitHub Actions free-tier runner.

**Note on Spec Typo**: Spec FR-006 contains a typo ("limit of hours"). This plan enforces the corrected value of **6 hours** as per the project's resource constraints and US-2.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `beir`, `sentence-transformers` (CPU-only), `datasketch` (MinHash-LSH), `scikit-learn`, `scipy`, `pandas`, `numpy`, `pytest`, `nltk` (WordNet), `beir`  
**Storage**: Local filesystem (`data/`), GitHub Actions ephemeral storage  
**Testing**: `pytest` (unit tests for clustering logic, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research/Computational Pipeline  
**Performance Goals**: Total runtime ≤ 6h, Peak RAM ≤ 7GB, Disk usage ≤ 14GB  
**Constraints**: No GPU/CUDA; no large-LLM training; all embeddings via `all-MiniLM-L6-v2` (CPU); strict adherence to spec FR-001 through FR-009.  
**Scale/Scope**: N=100 candidates per run; A set of synthetic clusters; random seeds for statistical testing. Budgets: low and medium tiers.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

| Principle | Compliance Status | Implementation Action |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; BEIR datasets fetched via `beir` library (canonical source); `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | PASS | Citations to BEIR and MinHash literature will be validated by Reference-Validator; no fabricated URLs used. WordNet (NLTK) cited for synonym replacement. |
| **III. Data Hygiene** | PASS | Raw BEIR data preserved in `data/raw/`; synthetic redundancy injected into `data/processed/`; checksums recorded in state file. |
| **IV. Single Source of Truth** | PASS | All metrics (NDCG, wasted ratio) derived from `data/` rows; no hand-typed numbers in `paper/`. Spec FR-006 typo noted and corrected to 6h. |
| **V. Versioning Discipline** | PASS | Content hashes tracked for all artifacts; state file updated on changes. |
| **VI. Active-Ranker Efficiency Accounting** | PASS | FR-003 & FR-006 implement explicit "wasted/informative" classification. **Clarification**: Cosine > 0.95 is the *definitive operational classification* for the main loop. Stratified sampling from *all* calls is used for *scientific validation* of this proxy. |
| **VII. Resource-Constrained Execution** | PASS | FR-006 (corrected to 6h) enforces limits; MinHash-LSH and `all-MiniLM-L6-v2` selected specifically for CPU feasibility. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-prp-redundancy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-873-llmxive-follow-up-extending-active-learn/
├── code/
│   ├── __init__.py
│   ├── config.py              # Hyperparameters, paths, seeds
│   ├── data_loader.py         # BEIR fetching, synthetic redundancy injection
│   ├── clustering.py          # MinHash-LSH implementation
│   ├── ranker.py              # Active PRP ranker wrapper
│   ├── metrics.py             # NDCG, wasted call ratio, statistical tests
│   └── run_pipeline.py        # Main orchestration script
├── data/
│   ├── raw/                   # Downloaded BEIR corpus
│   └── processed/             # Synthetic redundancy datasets
├── tests/
│   ├── unit/
│   │   ├── test_clustering.py
│   │   └── test_metrics.py
│   └── integration/
│       └── test_full_pipeline.py
└── requirements.txt
```

**Structure Decision**: Single-project structure chosen to minimize overhead. All logic resides in `code/` with clear separation of concerns (data, clustering, ranking, metrics). This aligns with the research nature of the feature and simplifies reproducibility.

## Complexity Tracking

No complexity violations identified. The plan adheres strictly to the spec's constraints and the project constitution.