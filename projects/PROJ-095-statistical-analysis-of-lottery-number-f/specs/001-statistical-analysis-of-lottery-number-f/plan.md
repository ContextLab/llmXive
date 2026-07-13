# Implementation Plan: Lottery Draw Integrity and Anomaly Detection

**Branch**: `001-lottery-draw-integrity` | **Date**: 2026-07-08 | **Spec**: `specs/001-lottery-draw-integrity/spec.md`
**Input**: Feature specification from `/specs/001-lottery-draw-integrity/spec.md`

## Summary

This feature implements a statistical analysis pipeline to assess lottery draw integrity by calculating specific "human-bias" metrics (Birthday Clustering and Consecutive Patterns) for each draw. The core analysis tests whether these metrics deviate from expected randomness in correlation with jackpot magnitude. The system explicitly acknowledges that it cannot control for Quick Pick rates due to data limitations, and therefore strictly limits its scope to "Draw Integrity" (machine fairness) rather than "Player Behavior". The implementation includes robustness checks via bootstrapping and sensitivity analysis on clustering thresholds, all designed to run on CPU-only GitHub Actions runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `pyyaml`  
**Storage**: Local CSV files (`data/raw/`, `data/processed/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Data Analysis CLI / Script  
**Performance Goals**: Complete analysis of historical dataset (approx. 500MB max) within 6 hours.  
**Constraints**: No GPU usage; no external API calls during CI (data must be pre-fetched or cached); memory usage < 7GB.  
**Scale/Scope**: Single dataset ingestion, statistical correlation, -iteration bootstrapping.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | All random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. Data fetched from canonical sources. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` will be validated against primary sources. No unverified dataset URLs will be used. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data stored in `data/raw/` with checksums. Derivations written to `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | **COMPLIANT** | All statistics in output derived from `data/processed/` rows. No hand-typed numbers in final reports. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts tracked via content hashes. `updated_at` timestamps updated on change. |
| **VI. Causal Inference Rigor** | **NOT APPLICABLE** | Constitution Principle VI mandates control for Quick Pick rates. However, public data sources do not contain `quick_pick_rate`. This variable is unobservable. Therefore, the requirement to "explicitly control" for it is mathematically impossible to fulfill. The plan **explicitly excludes** this principle from its scope, limiting all claims to "Draw Integrity" (machine fairness) and acknowledging that "Player Behavior" confounding cannot be controlled. No causal claims regarding player behavior will be made. |

## Project Structure

### Documentation (this feature)

```text
specs/001-lottery-draw-integrity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-095-statistical-analysis-of-lottery-number-f/
├── data/
│   ├── raw/             # Downloaded CSVs (checksummed)
│   └── processed/       # Derived datasets (bias metrics, etc.)
├── code/
│   ├── __init__.py
│   ├── ingestion.py     # FR-001: Download and parse
│   ├── metrics.py       # FR-002: Bias metric calculation (Birthday, Consecutive)
│   ├── correlation.py   # FR-004: Correlation analysis
│   ├── validation.py    # FR-005, FR-006, FR-007: Bootstrapping & Sensitivity
│   └── main.py          # Orchestration script
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── integration/     # End-to-end pipeline tests
│   └── unit/            # Metric calculation unit tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The analysis is a linear pipeline (Ingest -> Calculate -> Correlate -> Validate) best served by modular scripts within a single `code/` directory, avoiding the overhead of microservices for a batch statistical job.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bootstrapping (a sufficient number of iterations)** | Required for FR-005 to generate robust 95% CIs. | Analytical CIs assume normality which may not hold for small sample sizes or skewed jackpot distributions. |
| **Sensitivity Sweep** | Required for FR-006 to address arbitrary threshold concerns. | A single fixed threshold risks the "arbitrary cutoff" critique; sweeping a range of values proves robustness. |
| **Bonferroni Correction** | Required for FR-007 to control family-wise error rate. | Testing multiple bias patterns (birthday, consecutive, multiples) inflates Type I error; correction is statistically mandatory. |

## Addressing Unresolved Panel Concerns

**Concern**: Task T012 ('join raw draws with calculated metrics') depends on T011 ('calculate_rolling_uniformity_deviation'). Ambiguity exists regarding the output schema of T011 (rolling window vs. single draw row).

**Resolution**:
The plan explicitly redefines the metric calculation scope to ensure a **1:1 mapping** between input draws and output metrics, eliminating the need for a "rolling window" aggregation step in this specific feature.
1.  **Metric Definition**: The `draw_uniformity_deviation` (Chi-Square) was identified as scientifically invalid for single draws and has been **replaced** by `birthday_cluster_ratio` and `consecutive_pattern_count`. These are **per-draw** calculations.
2.  **Schema Alignment**:
    *   `ingestion.py` produces a `DrawRecord` per row.
    *   `metrics.py` takes a `DrawRecord` and outputs `birthday_cluster_ratio` and `consecutive_pattern_count` for that row.
    *   `correlation.py` performs a direct join on `draw_date` (or row index) because the metric is intrinsic to the draw.
3.  **Correction to Tasks**: The task `calculate_rolling_uniformity_deviation` has been renamed to `calculate_per_draw_bias_metrics` in the final `tasks.md` to reflect that the calculation is static per row, removing the ambiguity of window aggregation. The "rolling window" concept is entirely removed from the plan.

## Phased Implementation Plan

### Phase 0: Research & Data Strategy
*   **Goal**: Identify verified datasets and confirm variable availability.
*   **Activities**:
    *   Verify dataset sources for `winning_numbers`, `jackpot_amount`, and `total_sales` (FR-001).
    *   Confirm absence of `quick_pick_rate` in public sources (FR-003).
    *   Document dataset checksums and coverage dates.
*   **Output**: `research.md`, `data-model.md`.

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for ingestion and output.
*   **Activities**:
    *   Define `DrawRecord` schema with `birthday_cluster_ratio` and `consecutive_pattern_count`.
    *   Define `CorrelationResult` schema with metadata flags.
    *   Create YAML contracts for validation.
*   **Output**: `contracts/*.schema.yaml`.

### Phase 2: Implementation (Ingestion & Metrics)
*   **Goal**: Build `ingestion.py` and `metrics.py`.
*   **Activities**:
    *   Implement CSV parsing with missing data handling (Edge Case: Missing `total_sales`).
    *   Implement `birthday_cluster_ratio` (count of numbers <= 31 / total) and `consecutive_pattern_count` (count of adjacent pairs).
    *   Implement `is_majority_birthday` logic.
*   **Output**: `code/ingestion.py`, `code/metrics.py`.

### Phase 3: Correlation & Robustness
*   **Goal**: Build `correlation.py` and `validation.py`.
*   **Activities**:
    *   Implement Spearman/Pearson correlation with metadata flags (FR-004).
    *   Implement Bootstrapping (1000 iters) for CIs (FR-005).
    *   Implement Sensitivity Sweep for thresholds {, 0.6, 0.7} (FR-006).
    *   Apply Bonferroni correction (FR-007).
*   **Output**: `code/correlation.py`, `code/validation.py`.

### Phase 4: Integration & Testing
*   **Goal**: End-to-end execution and verification.
*   **Activities**:
    *   Run pipeline on sample data.
    *   Verify `birthday_cluster_ratio` against manual reference (SC-001).
    *   Verify CI width constraints (SC-004).
    *   Run on GitHub Actions runner to confirm feasibility.
*   **Output**: `tests/`, `research_review` artifacts.