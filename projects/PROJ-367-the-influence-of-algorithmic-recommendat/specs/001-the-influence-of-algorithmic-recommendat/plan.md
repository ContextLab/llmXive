# Implementation Plan: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Branch**: `001-the-influence-of-algorithmic-recommendations` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-the-influence-of-algorithmic-recommendations/spec.md`

## Summary

This project implements a methodological demonstration of an observational study design to quantify the association between the diversity of algorithmic course recommendations and subsequent learner enrollment diversity, controlling for baseline user interests. Due to the absence of a verified real-world educational dataset matching the required schema (distinct `recommended_categories` and `enrolled_categories` columns), the research component will be executed on a **synthetic dataset** generated to mimic realistic user-algorithm interactions. The technical approach involves ingesting data, computing Shannon entropy-based diversity metrics, applying Propensity Score Weighting (PSW) to balance observed confounders (with explicit diagnostics for positivity violations), and validating results via Outcome Permutation Tests and sensitivity analyses on semantic thresholds. All analysis is designed to run on CPU-first infrastructure (GitHub Actions free tier) using Python, `pandas`, `scikit-learn`, and `statsmodels`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `datasets` (Hugging Face), `pyyaml`, `pytest`  
**Storage**: Local CSV/Parquet files within the runner's ephemeral disk; checksums persisted to `state.yaml` immediately after download.  
**Testing**: `pytest` (unit tests for entropy calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU cores, ~7 GB RAM).  
**Project Type**: Data analysis pipeline / CLI.  
**Performance Goals**: Complete pipeline (ingestion, modeling, robustness) within 6 hours on CPU.  
**Constraints**: Must handle missing data gracefully; must detect and flag collinearity (VIF > 5); must avoid causal language in output; must handle PSW instability with a fallback to robust linear regression.  
**Scale/Scope**: Designed for large-scale datasets; assumes open, programmatic data access (or synthetic generation if no verified source exists).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **PASS**. The plan mandates pinned `requirements.txt`, random seed fixation (`numpy.random.seed`, `pandas`), and re-runnable scripts. Data will be fetched via canonical Hugging Face URLs or generated synthetically with a fixed seed.
- **II. Verified Accuracy**: **PARTIAL (Methodology Only)**. The plan acknowledges that no verified real-world educational dataset matching the schema exists in the provided list. Consequently, the "Verified Accuracy" principle applies to the *methodological pipeline* and *synthetic data generation logic*, not to the empirical validation of the hypothesis against real human behavior. All citations in the research phase will be restricted to verified URLs for the *methodology* and *tools*, not for the specific educational data source.
- **III. Data Hygiene**: **PASS**. Raw data (or synthetic generation seed) will be checksummed. Derived files (entropy scores, weights) will be written to new files with documented derivation steps. Checksums of ephemeral files are persisted to the project `state.yaml` immediately after download/generation to ensure compliance before the runner terminates.
- **IV. Single Source of Truth**: **PASS**. All statistics in the final report will be generated directly from the `code/` output files, not hand-typed.
- **V. Versioning Discipline**: **PASS**. Artifacts will carry content hashes; the plan includes steps to record these in the state file.
- **VI. Causal Independence Validation**: **NOT APPLICABLE FOR REAL DATA**. The plan explicitly states that real-data validation of causal independence is impossible without a verified real-world dataset. For the synthetic demonstration, the generator is designed to ensure temporal separation between the `recommended_categories` (predictor) and `enrolled_categories` (outcome) to mimic the independence required by the hypothesis, but this is a property of the simulation, not observed reality.
- **VII. Behavioral Agency Preservation**: **PASS**. The methodology (PSW with diagnostics, Outcome Permutation Tests) is designed to detect null results and acknowledges that user agency may override algorithmic influence. The plan does not assume a positive correlation.

## Project Structure

### Documentation (this feature)

```text
specs/001-the-influence-of-algorithmic-recommendations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── tasks.md             # Phase 1 output (Design Artifact)
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Generated) - Note: Distinct from design artifact
```

### Source Code (repository root)

```text
projects/PROJ-367-the-influence-of-algorithmic-recommendat/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py             # Paths, seeds, thresholds
│   ├── ingestion.py          # Data loading, validation (FR-007)
│   ├── metrics.py            # Entropy calculation (FR-001, FR-009)
│   ├── modeling.py           # PSW, regression, VIF (FR-002, FR-003, FR-008)
│   ├── robustness.py         # Permutation, sensitivity (FR-004, FR-005)
│   └── main.py               # Pipeline orchestration
├── data/
│   ├── raw/                  # Downloaded datasets or synthetic seed files
│   └── processed/            # Derived CSVs/Parquets
├── tests/
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_ingestion.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── reports/              # Final results
```

**Structure Decision**: Single project structure selected. The domain is purely analytical (no web/mobile UI). Separation into `ingestion`, `metrics`, `modeling`, and `robustness` modules ensures modularity for testing and adheres to the "Single Source of Truth" principle by isolating transformation logic.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Propensity Score Weighting (PSW) | Required by spec (US-2) to control for the confounding effect of baseline interests, which are mechanically linked to recommendations. | Standard linear regression without weighting would produce biased estimates due to high correlation between baseline and recommendations. *Note: PSW is used with strict diagnostics and a fallback to robust regression if instability is detected.* |
| Outcome Permutation Test | Required by spec (US-3) to validate results against unmeasured confounders in an observational setting. | Residual permutation was rejected as invalid for unmeasured confounders; shuffling the outcome variable provides a valid null distribution for the association. |
| Sensitivity Analysis Sweep | Required by spec (US-3) to justify the semantic similarity threshold. | A single threshold choice is arbitrary and vulnerable to criticism; a sweep demonstrates stability and bounds uncertainty. |
| E-value Calculation | Added to address unmeasured confounding limitations of PSW. | PSW alone cannot rule out unmeasured confounders; E-values quantify the robustness of the association. |

## Methodological Rigor & Assumptions

- **Causal Framing**: All results are framed as **associational** (FR-006). The plan explicitly acknowledges that PSW relies on the "Strong Ignorability" assumption, which is likely violated in real-world educational data. The study does not claim to prove causality.
- **Unmeasured Confounding**: The plan includes an **E-value** calculation to quantify the minimum strength of association an unmeasured confounder would need to have with both the treatment and the outcome to explain away the observed effect.
- **Positivity Violation**: The plan includes diagnostics to detect extreme weights (>10x median) and a fallback to Generalized Least Squares (GLS) with robust standard errors if the propensity model fails to converge or produces unstable weights.
- **Semantic Threshold**: The entropy metric is sensitive to the semantic similarity threshold. The plan justifies the sweep range (small, medium, large) based on standard NLP practices and explicitly frames the sensitivity analysis as bounding the uncertainty of the metric, rather than assuming a single "correct" threshold.
- **Temporal Independence**: The synthetic data generator ensures that `recommended_categories` are derived from a *prior* state of the user profile, distinct from the `enrolled_categories` of the current session, to mimic the independence required by the hypothesis.
