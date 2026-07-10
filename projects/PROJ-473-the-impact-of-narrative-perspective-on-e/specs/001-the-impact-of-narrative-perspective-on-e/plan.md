# Implementation Plan: The Impact of Narrative Perspective on Empathy and Moral Judgement

**Branch**: `001-narrative-perspective-empathy` | **Date**: 2026-07-03 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-narrative-perspective-empathy/spec.md`

## Summary

This project investigates the association between narrative perspective (first-person vs. third-person) in fictional texts and readers' empathic engagement and moral judgments. The technical approach involves:
1.  **Feature Extraction**: Using `spaCy` to quantify pronoun density and calculate a continuous `perspective_score`.
2.  **Data Linkage**: Employing TF-IDF similarity matching (excluding pronouns) to align stories with external moral judgment datasets for validation, while relying on verified external reader-response datasets (e.g., OSF, Moral Foundations Twitter) for the main analysis.
3.  **Statistical Analysis**: Conducting linear regression with Bonferroni corrections, VIF checks, and confounder control (genre, year) to test the hypothesis.
4.  **Sensitivity Analysis**: Sweeping similarity thresholds to ensure robustness.

The implementation is designed to run entirely on CPU within the GitHub Actions free-tier constraints (limited CPU resources, constrained RAM, time limit).

**Critical Distinction**: Synthetic data is used *only* for the "Independent Test" of the statistical engine (US-3) to verify code correctness. The primary scientific analysis relies exclusively on real-world data from verified external sources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `spaCy` (en_core_web_sm), `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `statsmodels`, `langdetect`, `pyyaml`, `requests`  
**Storage**: Local CSV/JSON files in `data/` and `artifacts/`  
**Testing**: `pytest` (unit tests for extraction logic; integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research Analysis Pipeline / CLI Tool  
**Performance Goals**: Total runtime ≤ 45 minutes; Peak memory < 6 GB.  
**Constraints**: 
- No GPU usage.
- **Constitution Principle VI (Text-Similarity Independence)**: Strict separation of features used for matching vs. analysis.
- **Constitution Principle III (Data Hygiene)**: PII scanning is a mandatory, blocking gate in the CI pipeline.
- **Constitution Principle V (Versioning Discipline)**: Artifact hashes are computed and the `state` file is updated automatically upon artifact generation.
**Scale/Scope**: Processing ~ short stories; generating statistical summaries and visualizations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin all versions. Random seeds (e.g., `np.random.seed(42)`) will be set in `code/`. External datasets will be fetched via verified URLs or loaders. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` will reference only the URLs provided in the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data will be checksummed. Transformations will produce new files. **PII scanning is a mandatory, blocking gate** in the CI pipeline; commits failing this check are rejected. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the paper will be generated directly from `data/` by scripts in `code/`. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. **The `state` file will be updated automatically** by a dedicated script after every artifact generation step, ensuring the `updated_at` timestamp and `artifact_hashes` map are current. |
| **VI. Text-Similarity Independence** | **PASS** | **Critical Implementation Rule**: The TF-IDF vector construction for matching (US-2) will explicitly exclude pronoun-based features (FR-008). The `perspective_score` (US-1) will be calculated independently. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-narrative-perspective-on-e/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Defined DURING Phase 1 to guide Phase 2)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── data_loader.py       # Fetches/loads datasets (OSF, Gutenberg)
├── extraction.py        # Pronoun density, TF-IDF (FR-001, FR-002, FR-008)
├── matching.py          # Similarity logic (US-2)
├── analysis.py          # Regression, VIF, Bonferroni, Confounder Control (FR-003, FR-004, FR-007)
├── visualization.py     # Scatter plots (FR-005)
├── main.py              # Orchestration script
└── utils.py             # Logging, validation helpers, PII scanning

data/
├── raw/                 # Downloaded external datasets
├── processed/           # Cleaned CSVs, extracted features
└── artifacts/           # Plots, sensitivity analysis reports

tests/
├── test_extraction.py
├── test_matching.py
├── test_analysis.py
└── test_pii_scan.py
```

**Structure Decision**: Single `code/` directory structure chosen for simplicity and direct execution on CI. Contracts are defined *during* Phase 1 and serve as inputs for the implementation phase (Phase 2).

## Complexity Tracking

No violations detected. The separation of concerns (Extraction vs. Matching vs. Analysis) aligns with the complexity of the research question and the need to avoid circularity (Constitution Principle VI). The CPU-only constraint is met by using `scikit-learn` and `statsmodels` which are lightweight and efficient. The plan explicitly distinguishes between pipeline validation (synthetic) and scientific discovery (real data).