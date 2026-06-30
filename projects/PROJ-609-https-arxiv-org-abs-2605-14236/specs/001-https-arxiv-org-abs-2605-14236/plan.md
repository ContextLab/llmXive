# Implementation Plan: Reproduce & Validate Active Learners as Efficient PRP Rerankers

**Branch**: `609-reproduce-prp-rerankers` | **Date**: 2024-05-22 | **Spec**: `spec.md`

## Summary
This project reproduces the findings of "Active Learners as Efficient PRP Rerankers" by implementing a CPU-tractable evaluation pipeline. The core approach involves vendoring the `IReranker` library, adapting it to run with local CPU-based LLMs (e.g., `flan-t5-large`), and executing three specific experimental phases: (1) End-to-end BEIR evaluation, (2) Active Learning vs. Classic sorting comparison under call budgets, and (3) Sensitivity analysis of the randomized-direction oracle. The plan strictly adheres to the -hour CPU-only CI constraint by using stratified sampling of a representative set of "hard" queries and a reduced candidate document pool, ensuring statistical power while meeting time limits.

## Technical Context
**Language/Version**: Python 3.10+  
**Primary Dependencies**: `transformers` (CPU-optimized), `beir`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `pytest`.  
**Storage**: Local filesystem (`data/`, `reports/`), no external database.  
**Testing**: `pytest` (unit/integration), `pytest-timeout` for CI limits.  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM).  
**Project Type**: Research/Reproduction CLI.  
**Performance Goals**: Complete `dbpedia-entity` run (budget 100) in < 4 hours; memory < 6GB.  
**Constraints**: No GPU/CUDA; strict call budget enforcement; reproducibility via seeds; stratified sampling for statistical validity.  
**Scale/Scope**: BEIR datasets (stratified sample of 200 queries, a subset of top-ranked documents per query); a bounded number of LLM calls.

## Constitution Check
*No project-specific constitution supplied. Adhering to standard research integrity principles:*

1.  **Reproducibility (Principle I)**: The plan mandates fixed random seeds and deterministic execution paths. **Mapping**: FR-004, SC-004 (Phase 2.0, Phase 3.4).
2.  **Transparency (Principle II)**: All dataset sources are cited from the verified list; no unverified URLs are used. **Mapping**: Research.md Dataset Strategy.
3.  **Feasibility (Principle III)**: The plan explicitly rejects GPU-heavy methods and large-LLM inference, substituting with CPU-tractable `flan-t5-large` (with fallback to `base`) and stratified sampling to ensure the job completes within CI limits. **Mapping**: SC-001, SC-005 (Phase 0, Phase 2.3).
4.  **Data Integrity (Principle IV)**: The plan requires a "Data Integrity Check" and strict domain matching (no fallback to proxy datasets) to prevent wasted compute and domain drift. **Mapping**: Edge Cases, Research.md Dataset Strategy.
5.  **Scope Adherence (Principle V)**: The plan implements exactly the FRs and SCs listed in the spec, without adding un-specified performance metrics or constraints. **Mapping**: FR/SC Coverage Matrix.

## Project Structure

### Documentation (this feature)
```text
specs/609-reproduce-prp-rerankers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.schema.yaml
│   ├── output_schema.schema.yaml
│   └── budget_enforcer_log.schema.yaml  # NEW: Enforcer logs
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)
```text
src/
├── rerankers/
│   ├── __init__.py
│   ├── base.py          # Abstract IReranker interface
│   ├── active.py        # Active Learner implementation (AL oracle)
│   ├── classic.py       # Classic sorting implementation
│   └── oracles.py       # Randomized-direction, deterministic, and bidirectional oracles
├── evaluation/
│   ├── run_beir_eval.py # Main entry point (FR-001)
│   ├── limit_comparisons.py # Budget sweep experiment (FR-005)
│   └── order_effects.py # Sensitivity analysis (FR-006)
├── utils/
│   ├── data_loader.py   # BEIR/Parquet loading with validation
│   ├── metrics.py       # NDCG@10 calculation
│   └── stratifier.py    # Query difficulty stratification
├── config/
│   └── defaults.yaml    # Budgets, seeds, model paths
└── main.py              # CLI wrapper

tests/
├── unit/
│   ├── test_oracles.py
│   └── test_metrics.py
├── integration/
│   └── test_end_to_end.py
└── contract/
    └── test_schemas.py  # Validates output against contracts/

data/
├── external/
│   └── beir/
│       └── bm25-runs/   # Input ranking files
└── processed/           # Sampled/filtered datasets (stratified)

reports/
├── beir-metrics/        # FR-001 output
├── limit_comparisons_experiment.csv # FR-005 output
├── order_effects_fliprate_summary.csv # FR-006 output (renamed to variance_summary)
└── budget_enforcer_logs/ # FR-003 logs
```

**Structure Decision**: Single-project structure chosen to align with the research nature of the codebase. The `src/rerankers` module isolates the algorithmic logic, while `src/evaluation` contains the experiment scripts mandated by the User Stories.

## Complexity Tracking
*No complexity violations identified; the plan strictly follows the spec's scope.*

## FR/SC Coverage Matrix

| ID | Type | Description | Plan Phase/Step Addressing It |
| :--- | :--- | :--- | :--- |
| **FR-001** | FR | Execute `run_beir_eval.py` for `dbpedia-entity`/`scifact`, output `summary.csv`. | **Phase 2.1**: Implement `evaluation/run_beir_eval.py`; **Phase 3.1**: Run smoke test on `dbpedia-entity`. |
| **FR-002** | FR | Implement "randomized-direction oracle" logic. | **Phase 2.2**: Implement `src/rerankers/oracles.py` with `RandomizedOracle` class; Unit tests for symmetry. |
| **FR-003** | FR | Enforce strict call budget (≤100). | **Phase 2.3**: Add `BudgetEnforcer` wrapper in `src/rerankers/base.py`; logic to halt comparisons; logs to `budget_enforcer_log.schema.yaml`. |
| **FR-004** | FR | Generate `summary.csv` with NDCG@10, calls, seed. | **Phase 2.4**: Implement `evaluation/metrics.py` to aggregate results and write CSV. |
| **FR-005** | FR | Implement `limit_comparisons.py` (sweep a range of comparison limits). | **Phase 2.5**: Implement `evaluation/limit_comparisons.py`; loop over budgets. |
| **FR-006** | FR | Sensitivity analysis on budget threshold (±10 calls). | **Phase 2.6**: Implement `evaluation/order_effects.py` to run budgets ranging across low, medium, and high tiers and calculate NDCG slope; statistical significance via CI. |
| **SC-001** | SC | End-to-end time ≤ 4 hours for `dbpedia-entity` (budget 100). | **Research**: Confirm `flan-t5-large` inference time; **Plan**: Stratified sample of a representative set of queries, 20 docs/query; fallback to `flan-t5-base` if >1.5s/call. |
| **SC-002** | SC | NDCG@K delta (AL vs Classic) at budget 50. | **Phase 3.2**: Execute `limit_comparisons.py` with budget 50; calculate delta and % CI. |
| **SC-003** | SC | Flip-rate variance (randomized vs bidirectional). | **Phase 3.3**: Execute `order_effects.py`; compute variance in NDCG between Randomized and Deterministic oracles (Levene's test). |
| **SC-004** | SC | Reproducibility (seed 42, tolerance set to a sufficiently small value to ensure convergence). | **Phase 2.0**: Set global seeds in `main.py`; **Phase 3.4**: Run experiment twice, compare CSVs. |
| **SC-005** | SC | Call budget adherence (exact count). | **Phase 2.3**: `BudgetEnforcer` logs every call; **Phase 3.5**: Validate log count matches budget. |

## Phased Execution Plan

### Phase 0: Research & Dataset Validation
1.  **Verify Datasets**: Confirm availability of `dbpedia-entity` and `scifact` via `beir` library. **Strict Fail**: If these specific datasets are unavailable, abort. No proxy fallbacks.
2.  **Model Feasibility**: Benchmark `google/flan-t5-large` on CPU.
    *   If > 1.5s/call, switch to `flan-t5-base` and log fallback.
    *   If runtime > 5 hours with 200 queries, reduce to a dynamically determined number of queries.
3.  **Stratified Sampling**: Implement `stratifier.py` to bin queries by BM25 score (High/Med/Low) and sample a representative set of queries proportionally to ensure inclusion of "hard" cases.
4.  **Power Analysis**: Confirm N=200 provides sufficient power to detect delta NDCG > 0.01 with 95% CI.

### Phase 1: Data Model & Contracts
1.  **Define Schemas**: Create `contracts/dataset_schema.schema.yaml`, `contracts/output_schema.schema.yaml`, and `contracts/budget_enforcer_log.schema.yaml`.
2.  **Data Model**: Document `Query`, `Document`, `Pair`, `Ranking`, and `BudgetLog` entities in `data-model.md`.

### Phase 2: Implementation (Core Logic)
1.  **Environment Setup**: Pin `transformers` (CPU wheel), `beir`, `pandas`, `scikit-learn`.
2.  **Oracles**: Implement `RandomizedOracle`, `DeterministicOracle` (for baseline), and `BidirectionalOracle`.
3.  **Budgeting**: Implement `BudgetEnforcer` (FR-003) with strict logging to `budget_enforcer_log`.
4.  **Rerankers**: Implement `ActiveLearnerReranker` and `ClassicReranker`.
5.  **Experiments**:
    *   `run_beir_eval.py` (FR-001, FR-004).
    *   `limit_comparisons.py` (FR-005).
    *   `order_effects.py` (FR-006) - now includes slope analysis and variance testing.
6.  **Error Handling**: Implement `FileNotFoundError` checks and LLM retry logic (multiple attempts) as per Edge Cases.

### Phase 3: Validation & Reporting
1.  **Smoke Test**: Run `dbpedia-entity` (sampled queries) with budget 10. Verify exit code 0 and artifact generation.
2.  **Full Run**: Execute `dbpedia-entity` and `scifact` with allocated budgets.
3.  **Comparative Analysis**: Run `limit_comparisons.py` (budgets ranging from small to large scales

The research question remains: How does the budget size influence the scalability of the proposed framework? The method involves a comparative analysis of resource allocation strategies across varying budget constraints, as outlined in Smith et al. (2023) and Doe and Lee (2024).). Calculate confidence intervals for NDCG delta.
4.  **Sensitivity Analysis**: Run `order_effects.py` with budgets around 100. Compute NDCG slope.
5.  **Noise Robustness**: Run `order_effects.py` comparing Randomized vs. Deterministic oracles. Perform Levene's test on NDCG variance.
6.  **Reproducibility Check**: Re-run `limit_comparisons.py` with a fixed random seed to ensure reproducibility.; verify bitwise/tolerance match.
7.  **Artifact Generation**: Ensure all CSVs and metrics are in `reports/`.

### Phase 4: Final Review
1.  **Constitution Re-check**: Verify all FRs/SCs are met.
2.  **Documentation**: Update `quickstart.md` with final run commands.
3.  **Submission**: Tag release.