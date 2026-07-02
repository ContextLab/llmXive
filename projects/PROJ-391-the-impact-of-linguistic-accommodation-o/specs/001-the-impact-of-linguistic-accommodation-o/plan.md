# Implementation Plan: The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

**Branch**: `001-linguistic-accommodation-empathy` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-linguistic-accommodation-empathy/spec.md`

## Summary

This project implements a computational pipeline to investigate the correlation between linguistic accommodation (lexical and syntactic similarity) and *emotional congruence* (a proxy for perceived empathy) in dialogue. The technical approach involves: (1) ingesting and normalizing dialogue data (DailyDialog, treated as a proxy for AI-Human interaction where the second turn simulates the AI); (2) computing Jaccard-based lexical overlap and POS-tag-based syntactic similarity metrics, with a filter for exact repetition; (3) deriving a 'Proxy Empathy Score' via an emotion-to-Likert mapping rule where explicit ratings are missing; (4) performing Pearson/Spearman correlation analyses with bootstrap resampling for robustness; and (5) controlling for conversation length and topic (using dataset-provided labels) via regression. All analyses will be conducted using CPU-tractable Python libraries (`scikit-learn`, `scipy`, `pandas`, `nltk`, `spacy`) to ensure execution within the 6-hour, 7GB RAM, 2-core GitHub Actions free-tier constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `nltk`, `matplotlib`, `seaborn`, `pyyaml`, `datasets`, `spacy` (for dependency parsing), `jsonschema` (for contract validation)  
**Storage**: Local CSV/JSON artifacts under `data/`; no persistent database.  
**Testing**: `pytest` for unit tests on metric computation; integration tests for pipeline stages.  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Research Data Pipeline / Statistical Analysis  
**Performance Goals**: Complete full pipeline (ingestion to visualization) in < 6 hours on 2 vCPU.  
**Constraints**: No GPU; memory usage < 7 GB; must handle missing data gracefully; all random seeds pinned for reproducibility.  
**Scale/Scope**: Processing the full DailyDialog test set (approx. tens of thousands of turns) and derived metrics.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Random seeds (`numpy.random.seed`, `random.seed`) pinned in `code/`. `requirements.txt` strictly pins versions. Data checksums recorded in `state/projects/PROJ-391-the-impact-of-linguistic-accommodation-o.yaml` before processing. |
| **II. Verified Accuracy** | Citations in `research.md` and `paper/` will be validated against primary sources (Giles et al., 2003; DailyDialog original paper) by the **Reference-Validator Agent**. A pre-analysis gate in the pipeline runs this agent before any statistical computation. |
| **III. Data Hygiene** | Raw data (DailyDialog) stored in `data/raw/` with checksum. Derived metrics stored in `data/processed/` with new filenames. No in-place modification. PII scan passed on all commits. |
| **IV. Single Source of Truth** | All statistics in the final report are programmatically generated from `data/processed/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | Artifact hashes tracked in `state/projects/PROJ-391-the-impact-of-linguistic-accommodation-o.yaml`. Changes to `code/` or `data/` trigger timestamp updates. |
| **VI. Human Subject Ethics** | The project uses public, anonymized data (DailyDialog). The "human ratings" are derived from existing dataset annotations (emotion labels) or inferred via rules. **No new human data collection is performed.** FR-010 is satisfied by using the dataset's existing labels as the validation proxy (n=full dataset) and a spot-check of a sample of pairs. No IRB required for secondary analysis of public data. |
| **VII. Statistical Validity** | Hypotheses pre-registered in `spec.md`. Effect sizes (correlation coefficients) reported with 95% CIs. Bonferroni correction applied for multiple comparisons (a set of tests). Effect size interpretation (Cohen's guidelines) is mandatory to avoid trivial significance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-linguistic-accommodation-o/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-391-the-impact-of-linguistic-accommodation-o/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_ingestion.py        # Loads DailyDialog, normalizes, computes raw metrics, filters repetition
│   ├── empathy_mapping.py       # Applies emotion-to-Likert rules
│   ├── statistical_analysis.py  # Correlations, regression, bootstrap (iterative loop), effect size interpretation
│   ├── sensitivity_analysis.py  # Compares POS vs. Dependency parse metrics
│   ├── utils.py                 # Normalization, POS tagging, Jaccard helpers, Dependency parsing
│   └── main.py                  # Pipeline orchestration (includes Contract Validation and Reference-Validator gate)
├── data/
│   ├── raw/                     # Downloaded DailyDialog (checksummed)
│   └── processed/               # Derived CSVs (metrics, empathy ratings)
├── tests/
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_empathy_mapping.py
│   └── integration/
│       └── test_pipeline.py
└── outputs/
    ├── figures/                 # Scatter plots, distributions
    └── reports/                 # Statistical summaries
```

**Structure Decision**: Single project structure chosen. The workflow is linear (Ingest -> Map -> Analyze -> Visualize) and fits well within a single codebase without needing microservices or complex separation. `code/` contains all logic; `data/` separates raw vs. processed; `tests/` validates each stage.

## Pipeline Steps & Contract Validation

1.  **Pre-Analysis Gate**: Run `Reference-Validator Agent` to verify all citations in `research.md` and `plan.md`. If any citation fails, abort.
2.  **Ingestion**: `data_ingestion.py` loads data, normalizes (NFKC), filters empty/non-text, and **filters exact repetitions** (Jaccard > 0.9). Computes lexical and POS metrics. **Validates output against `contracts/dataset.schema.yaml`**.
3.  **Empathy Mapping**: `empathy_mapping.py` applies the emotion-to-Likert rule. **Validates output against `contracts/dataset.schema.yaml`**.
4.  **Sensitivity Analysis**: `sensitivity_analysis.py` computes dependency-parse metrics and compares with POS metrics.
5.  **Statistical Analysis**: `statistical_analysis.py` runs correlations, regression (with dataset-provided topic labels), and **iterative bootstrap** (loop until CI width < 0.01 or max iterations). Applies Bonferroni correction and **interprets effect sizes** (Cohen's guidelines). **Validates output against `contracts/output.schema.yaml`**.
6.  **Visualization**: Generates plots.
7.  **Validation Subset**: Samples a sufficient number of pairs and compares inferred scores against original labels. (consistency check).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bootstrap Resampling (Iterative Loop)** | Required by FR-006 to ensure 95% CI width < 0.01. | A fixed iteration count (e.g., 1000) does not guarantee the CI width requirement. |
| **POS-based vs. Dependency Parse Sensitivity** | Required by FR-009 to validate construct validity. | Relying solely on POS would ignore potential nuances in syntactic structure that dependency parsing captures, risking invalid proxy claims. |
| **Multiple Comparison Correction** | Required by FR-005/SC-005 for 4 hypothesis tests. | Ignoring family-wise error rate would inflate Type I error, violating Principle VII (Statistical Validity). |
| **Repetition Filter** | Required to distinguish accommodation from simple repetition. | Without this, high lexical overlap might reflect a failure mode (repetition) rather than genuine accommodation. |
| **Effect Size Interpretation** | Required to avoid p-hacking in large-N data. | Statistical significance alone is insufficient; trivial effects must be flagged as negligible. |
| **Dataset-Provided Topic Labels** | Required to avoid unstable LDA. | LDA on short turns is noisy; dataset labels are ground truth for topic. |

## Limitations & Assumptions (Revised)

- **Dataset Proxy**: DailyDialog is Human-Human. The study treats the second turn as a "proxy AI response". Findings are about dialogue accommodation, not specifically AI.
- **Construct Validity**: The "Empathy Score" is a proxy derived from emotion labels. The analysis tests "Accommodation vs. Emotional Congruence".
- **Topic Confounding**: Topic is controlled using dataset labels, not LDA.
- **No New Human Collection**: FR-010 is satisfied by using existing dataset labels as the validation proxy.
