# Implementation Plan: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

**Branch**: `001-code-maintainability-impact` | **Date**: 2026-07-08 | **Spec**: `specs/001-code-maintainability-impact/spec.md`
**Input**: Feature specification from `/specs/001-code-maintainability-impact/spec.md`

## Summary

This project evaluates whether code blocks classified as "LLM-generated" exhibit different long-term maintainability characteristics compared to "Human-written" code blocks. The approach involves:
1.  **Curation**: Identifying active Python/JS repositories via GitHub API and extracting metadata (stars, age, total LOC).
2.  **Classification**: Using a pre-trained CodeBERT model (`microsoft/codebert-base`, ONNX runtime) to tag code blocks as "LLM" or "Human" with ≥0.8 confidence.
3.  **Matching**: Performing 1:1 propensity score matching on block-level complexity and repo-level covariates (stars, age, total LOC) to control for confounding variables.
4.  **Longitudinal Analysis**: Extracting code churn and bug fix latency over a multi-month window.
5.  **Statistical Testing**: Applying Wilcoxon Signed-Rank tests (paired) with Benjamini-Hochberg correction on matched pairs.

> **Critical Limitation Note**: This study is observational. The "LLM" label is a probabilistic proxy derived from code patterns, not a verified ground truth for generation method. Results are framed as "associational differences" between blocks with LLM-like patterns and human-like patterns, not causal impacts of LLMs.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `onnxruntime`, `radon`, `scikit-learn`, `pandas`, `matplotlib`, `pygithub`  
**Storage**: Local filesystem (`data/`), GitHub API (remote)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Data Analysis / Research Pipeline  
**Performance Goals**: Complete analysis within 6 hours on CPU-only runner; RAM usage < 6GB.  
**Constraints**: No GPU; no large model fine-tuning; strict adherence to GitHub API rate limits; datasets must fit in memory or be processed in streams.  
**Scale/Scope**: A set of repositories; A substantial number of code blocks; -month historical window.

**Model Source**: `microsoft/codebert-base` (HuggingFace) - Cited per Constitution Principle II.

> **Note on Dataset Strategy**: The project relies on the GitHub API for primary data ingestion (repositories, code blocks, issues, commit history). The "Verified datasets" block in the prompt contains generic LLM-text and JavaScript datasets which are **not** suitable for this specific longitudinal study (they lack commit history, issue links, and repo context). Therefore, the implementation **does not** use those external URLs as the primary data source. Instead, it programmatically fetches data from GitHub as specified in FR-001.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | Pass | Random seeds pinned in `code/`. GitHub API queries use fixed parameters. All dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | Pass | Model source (`microsoft/codebert-base`) explicitly cited. No external data citations; data fetched live from GitHub. |
| **III. Data Hygiene** | Pass | Raw API responses saved to `data/raw/` with checksums. Derived data in `data/processed/`. No in-place modification. PII scan enforced. |
| **IV. Single Source of Truth** | Pass | All figures/statistics derived from `data/processed/matched_pairs.csv` and `data/processed/metrics.csv`. |
| **V. Versioning Discipline** | Pass | Content hashes tracked in `state/`. Artifact changes trigger `updated_at` updates. |
| **VI. Longitudinal Data Integrity** | Pass | Time-series data captured via immutable snapshots of `git log` and GitHub Issues API. Gaps documented. **Note**: The Constitution mentions "Mann-Whitney U", but for *matched pairs* (FR-008), the Wilcoxon Signed-Rank test is the statistically correct method. This plan uses Wilcoxon Signed-Rank; the Constitution requires amendment to reflect the paired design. |
| **VII. Classification Ground Truth** | Pass | Random subset (minimum number of blocks) manually verified. Precision/Recall calculated and reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-code-maintainability-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── ground_truth_schema.schema.yaml
    ├── metrics.schema.yaml
    └── metrics_schema.schema.yaml
```

### Source Code (repository root)

```text
code/
├── 01_curation.py           # FR-001: Repo search, cloning, metadata extraction (stars, age, total_loc)
├── 02_classification.py     # FR-002: CodeBERT tagging (ONNX)
├── 03_matching.py           # FR-008: Propensity score matching (block + repo covariates)
├── 04_metrics.py            # FR-004: Churn & latency extraction
├── 05_analysis.py           # FR-005, FR-006: Wilcoxon tests, plots
├── 06_ground_truth.py       # FR-007: Manual verification subset selection
├── utils/
│   ├── git_utils.py         # Git log parsing, file tracking
│   ├── github_utils.py      # API wrappers
│   └── config.py            # Seeds, constants
├── requirements.txt
└── main.py                  # Orchestration script

data/
├── raw/                     # API dumps, git logs
├── processed/               # Matched pairs, metrics
└── ground_truth/            # Manual verification labels

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single project structure (`code/`) selected to simplify data flow between curation, classification, and analysis phases. No separate frontend/backend required as this is a batch research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Propensity Score Matching (PSM) | Required to control for confounding variables (complexity, repo size) to isolate the effect of code origin. | Simple t-tests on raw data would be biased by inherent complexity differences between LLM and human code. |
| Longitudinal Tracking | Required to measure "long-term" maintainability (churn, latency). | Cross-sectional analysis cannot capture maintenance burden over time. |
| ONNX Runtime | Required for CPU-only inference of CodeBERT within 6-hour limit. | Standard PyTorch inference is too slow on CPU for large codebases; GPU is unavailable. |

## Limitations & Assumptions

- **Selection Bias**: Repositories tagged `topic:llm-generated` may not represent general LLM usage. Results are limited to this population.
- **Ground Truth**: The "LLM" label is a probabilistic proxy. Misclassification risk is quantified via FR-007 but cannot be fully eliminated.
- **Developer Skill**: Matching within repositories controls for some team-level heterogeneity, but individual developer skill remains a potential confounder.
- **Latency Metric**: "Bug Fix Latency" measures issue resolution speed for *tracked* issues. It excludes untracked fixes and may be biased by issue severity.
- **Style Confounding**: Code style patterns (which the classifier detects) may directly influence churn metrics, confounding the "origin" effect.
- **Time Window**: A pragmatic temporal constraint is established for the study duration.; it may not capture full lifecycle effects.
- **Constitution Alignment**: The Constitution mentions "Mann-Whitney U" for comparisons, but the paired design (FR-008) requires Wilcoxon Signed-Rank. This plan uses Wilcoxon; the Constitution requires amendment.