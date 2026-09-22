# Implementation Plan: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Branch**: `001-the-influence-of-algorithmic-recommendations` | **Date**: 2026-07-30 | **Spec**: `specs/001-the-influence-of-algorithmic-recommendations/spec.md`
**Input**: Feature specification from `/specs/001-the-influence-of-algorithmic-recommendations/spec.md`

## Summary

This plan implements a statistical analysis pipeline to measure the associational relationship between the diversity of algorithmic course recommendations and subsequent learner enrollment diversity, controlling for baseline interests. The technical approach involves ingesting public enrollment data, calculating Shannon entropy (log base 2) for diversity metrics, applying Propensity Score Weighting (PSW) with Overlap Weighting fallback for extreme weights, and validating results via Residual Permutation Tests. **Crucially, this plan requires a verified educational dataset; if no such dataset is found, the project is blocked.**

**Key Revision**: The requirement for semantic similarity merging and threshold sensitivity analysis has been removed from the scope to avoid arbitrary category definitions without a verified ontology. Diversity is now calculated directly on the raw category labels provided in the dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pyyaml`, `datasets` (Hugging Face)  
**Storage**: Local filesystem (CSV/Parquet/JSON) within the CI runner's ephemeral storage (~14 GB limit).  
**Testing**: `pytest` with `pytest-cov` for unit tests and `pytest-mock` for data ingestion mocks.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Full pipeline execution < 6 hours on CPU; memory usage < 6 GB during peak processing. **The entire pipeline is designed to run within these constraints to ensure reproducibility on a fresh runner.**  
**Constraints**: No GPU usage; no causal language in final output; strict adherence to verified dataset URLs; handling of missing data as per spec. **No analysis will be performed on non-educational data.**  
**Scale/Scope**: Designed for datasets up to ~100k rows; handles streaming for larger datasets if available.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (Principle I)**: The plan mandates pinned dependencies in `requirements.txt` and the use of fixed random seeds in all stochastic processes (PSW, permutation tests). **Every result is reproducible by re-running the project's `code/` against the project's `data/` on a fresh GitHub Actions runner.** All external data sources are restricted to the "Verified datasets" block.
2.  **Verified Accuracy (Principle II)**: All citations in `research.md` will be restricted to the provided verified URLs. No external URLs will be invented.
3.  **Data Hygiene (Principle III)**: The plan specifies a `data/` directory structure where raw data is checksummed **and the checksum recorded under `data/` in the state YAML file**. No data may be modified in place; every transformation MUST produce a new file with a documented derivation.
4.  **Single Source of Truth (Principle IV)**: The `quickstart.md` and `data-model.md` will define the exact data flow from raw ingestion to final metrics, **ensuring every figure in the eventual report traces to a specific row in the processed data**. The schemas in `contracts/` enforce this by ensuring the output schema matches the data model and the code produces output that conforms to the schema.
5.  **Versioning Discipline (Principle V)**: The `plan.md` and `research.md` will reference the specific commit hash of the spec and the project ID. **Every artifact under this project carries a content hash.**
6.  **Causal Independence Validation (Principle VI)**: The plan explicitly separates the "recommendation" column (predictor) from the "enrollment" column (outcome) in the data model. **A verification step (automated schema check and statistical correlation test) ensures these columns are distinct and that the predictor is not mechanically derived from the outcome.** The methodology (PSW) is chosen specifically to address the confounding between these two, ensuring the predictor is not mechanically derived from the outcome in the analysis step.
7.  **Behavioral Agency Preservation (Principle VII)**: The analysis framework includes a "Null Result" handling path (SC-002, SC-003) where a lack of correlation is **treated as a significant, publishable finding** that challenges assumptions about the power of recommender systems in educational contexts.

## Scope Exclusion

**Game-Theoretic Constructs**: The plan explicitly excludes all game-theoretic constructs (e.g., Nash Equilibrium, utility functions, payoff structures) from the analysis scope. These theoretical constructs are not present in the spec or data and would risk violating FR-006's strict associational framing. The analysis will not introduce causal language or violate the 'Single Source of Truth' principle by deriving theoretical constructs not in the data.

**Semantic Similarity Merging**: The plan explicitly excludes the requirement to merge categories based on semantic similarity thresholds (0.01, 0.05, 0.1). Without a verified domain-specific ontology for the dataset, this step is arbitrary and invalidates the diversity metric. Diversity is calculated directly on the raw category labels provided in the dataset.

## Project Structure

### Documentation (this feature)

```text
specs/001-the-influence-of-algorithmic-recommendations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-367-the-influence-of-algorithmic-recommendat/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingestion.py          # Data loading and validation (FR-007)
│   ├── metrics.py            # Entropy calculation (FR-001)
│   ├── modeling.py           # PSW and Regression (FR-002, FR-003, FR-008)
│   ├── robustness.py         # Residual Permutation Test (FR-004)
│   └── report.py             # Final associational framing (FR-006)
├── data/
│   ├── raw/                  # Downloaded datasets (checksummed)
│   ├── processed/            # Derived features (entropy, weights)
│   └── results/              # Final metrics and plots
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_ingestion.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── data_dictionary.md
```

**Structure Decision**: A modular Python package structure (`code/`) is selected to support unit testing of individual components (entropy, PSW, permutation) and to facilitate the "Reproducibility" requirement. The separation of `ingestion`, `metrics`, and `modeling` ensures that the data flow is transparent and traceable, satisfying the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Propensity Score Weighting (PSW) with Overlap Weighting | The spec requires controlling for "baseline interests" which are highly correlated with recommendations. Simple regression would suffer from multicollinearity and bias. **Overlap weighting is used to handle extreme weights instead of falling back to biased standard regression.** | Simple linear regression was rejected because it cannot adequately balance the confounding effect of intrinsic user preferences, leading to spurious associations. **Falling back to standard linear regression when PSW fails is explicitly rejected as it reintroduces bias.** |
| Residual Permutation Test | The spec requires validating against unmeasured confounders in an observational study. Standard p-values are insufficient for robustness claims. **Outcome permutation is rejected as it ignores the weight structure.** | Standard bootstrap was rejected because it resamples data points rather than breaking the specific link between the treatment and the outcome, which is necessary to test the null hypothesis of no effect. **Outcome permutation is rejected because it fails to preserve the weight structure required for the confounder adjustment.** |
| Direct Entropy Calculation | The spec originally required semantic similarity merging, but this is arbitrary without a verified ontology. **Direct calculation on raw labels is the only valid approach.** | Semantic similarity merging was rejected because it requires a domain-specific ontology that is not available, making the metric arbitrary and invalid. |

## Data Availability Gate

**Critical Requirement**: The project **MUST** use a dataset containing distinct columns for `recommended_categories` and `enrolled_categories` with **educational course topics**. **No analysis will be performed on non-educational data** (e.g., robotics, code, medical data) as it constitutes a category error and invalidates the scientific claim. If no verified educational dataset is found in the "Verified datasets" block, **the project is blocked** and no further implementation will proceed. The `DataSchemaError` (FR-007) will be raised if the required columns are missing or if the dataset is not educational.

## Reproducibility of Fallbacks

**Overlap Weighting Fallback**: If extreme weights are detected (>10x median), the system applies Overlap Weighting (truncation or formula $w_i = 1 - p_i$). **The reproducibility of this fallback is ensured by logging the specific threshold used, the exact number of rows trimmed, and the resulting model parameters for the trimmed set.** This ensures the fallback is reproducible as per Principle I.

**Runtime Warning**: If the pipeline runtime exceeds 6 hours, a warning flag is recorded in the output. The pipeline is designed to be CPU-trivial to avoid this, but the error handling is a warning, not a hard crash, to allow for metric recording.