# Implementation Plan: Statistical Analysis of GitHub Issue Resolution Times

**Branch**: `001-github-issue-resolution` | **Date**: 2026-06-25 | **Spec**: `specs/001-github-issue-resolution/spec.md`
**Input**: Feature specification from `/specs/001-github-issue-resolution/spec.md`

## Summary

Statistical analysis of publicly available GitHub issue resolution times via REST API collection, distribution fitting (log-normal, Weibull), hypothesis testing with Holm-Bonferroni correction, and linear mixed-effects modeling with repository-level random intercepts. All analysis is associational/correlational due to observational design.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pandas`, `numpy`, `scipy`, `statsmodels`, `pymer4` (CPU-tractable), `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational-analysis  
**Performance Goals**: Complete within ≤6 hours runtime, ≤7GB RAM, ≤14GB disk  
**Constraints**: No GPU/CUDA, no 8-bit quantization, no deep network training  
**Scale/Scope**: ≥100 repositories, ≥1000 issues, ≥5 programming languages, ≥3 project size categories, ≥10 issues per repository

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Evidence/Mapping |
|------------------------|--------|------------------|
| I. Reproducibility | ✅ PASS | All code pinned in `requirements.txt`; random seeds set; data fetched from GitHub API on every run |
| II. Verified Accuracy | ✅ PASS | External citations validated via Reference-Validator; title overlap ≥0.7 threshold enforced |
| III. Data Hygiene | ✅ PASS | Data checksummed; raw data preserved; derivations produce new files; PII scan enforced |
| IV. Single Source of Truth | ✅ PASS | All figures/statistics trace to exactly one `data/` row and one `code/` block |
| V. Versioning Discipline | ✅ PASS | Content hashes recorded; `state/*.yaml` updated on artifact changes |
| VI. Temporal Data Integrity | ✅ PASS | Timestamps obtained directly from GitHub API; raw fields stored unchanged; timezone normalization via deterministic scripts |
| VII. Reproducible Feature Engineering | ✅ PASS | Predictors extracted via version-controlled scripts; API fields explicitly declared; identical outputs guaranteed |

## Project Structure

### Documentation (this feature)

```text
specs/001-github-issue-resolution/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── analysis.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── collect/
│   ├── fetch_issues.py          # GitHub API collection (FR-001)
│   └── preprocess.py            # Data cleaning, resolution time computation (FR-002, FR-003)
├── analyze/
│   ├── distributions.py         # ECDF, log-normal, Weibull fitting (FR-002)
│   ├── hypothesis_tests.py      # ANOVA, Kruskal-Wallis, Holm-Bonferroni (FR-004)
│   ├── mixed_effects.py         # LMM with random intercepts (FR-005)
│   ├── diagnostics.py           # VIF, collinearity, sensitivity analysis (FR-006, FR-007)
│   └── results.py               # Associational language enforcement (FR-008)
├── utils/
│   ├── api_client.py            # Rate limit handling, exponential backoff (FR-001)
│   ├── config.py                # Random seeds, paths, thresholds
│   └── validators.py            # Schema validation against contracts/
├── tests/
│   ├── contract/                # Schema contract tests
│   ├── integration/             # Pipeline integration tests
│   └── unit/                    # Unit tests for individual functions
└── requirements.txt             # Pinned dependencies

data/
├── raw/                         # Raw API responses (checksummed)
├── processed/                   # Cleaned, analysis-ready datasets
└── figures/                     # ECDF, diagnostic plots

state/
└── projects/PROJ-208-statistical-analysis-of-publicly-availab.yaml  # Artifact hashes, updated_at
```

**Structure Decision**: Single computational project structure selected. All analysis code resides under `code/` with clear separation of collection, preprocessing, analysis, and utilities. Tests organized by type (contract, integration, unit). Data organized by processing stage (raw → processed).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-effects modeling (not simple linear regression) | Repository-level variance must be captured; issues within same repo are not independent | Simple regression would violate independence assumption and produce invalid p-values |
| Holm-Bonferroni correction (not uncorrected tests) | ≥3 hypothesis tests conducted; family-wise error rate must be controlled | Uncorrected tests would inflate Type I error rate beyond acceptable threshold |
| VIF diagnostics (not skipping collinearity checks) | Predictors may be definitionally related (e.g., comments_count bounded by issue lifetime) | Ignoring collinearity would produce misleading effect size estimates |
| **comments_count endogeneity** | **comments_count accumulates during issue lifetime (partially determined by outcome)** | **Cannot claim independent effect; reported as descriptive association only (see Limitations)** |

## FR-SC Coverage Matrix

| Requirement | Plan Phase | Implementation File | Notes |
|-------------|------------|---------------------|-------|
| FR-001: Collect ≥100 repos via REST API | Phase 1: Data Collection | `code/collect/fetch_issues.py`, `code/utils/api_client.py` | Exponential backoff for rate limits |
| FR-002: Compute resolution time (hours), log-transform | Phase 1: Data Preprocessing | `code/collect/preprocess.py` | Log(x+1) for zero handling |
| FR-003: Exclude negative/missing resolution times | Phase 1: Data Preprocessing | `code/collect/preprocess.py` | Flagged and logged per SC-001 |
| FR-004: Holm-Bonferroni for ≥3 hypothesis tests | Phase 2: Hypothesis Testing | `code/analyze/hypothesis_tests.py` | Family-wise error rate control |
| FR-005: LMM with random intercepts for repository | Phase 2: Mixed Effects | `code/analyze/mixed_effects.py` | Repository-level variance captured |
| FR-006: VIF calculation, flag VIF≥5 | Phase 2: Diagnostics | `code/analyze/diagnostics.py` | Collinearity reported descriptively |
| FR-007: Sensitivity analysis (α=0.01, 0.05, 0.1) | Phase 2: Diagnostics | `code/analyze/diagnostics.py` | **Threshold sensitivity (status changes), not FP/FN rates (spec-root cause; flagged for kickback)** |
| FR-008: "Associational"/"correlational" in result text | Phase 2: Results | `code/analyze/results.py` | No causal claims permitted |
| FR-009: ≤6 hours, 2-CPU, 7GB RAM | All Phases | GitHub Actions free-tier | Runtime/memory monitored |
| FR-010: CPU-tractable only (no GPU/CUDA) | All Phases | `requirements.txt` pins | No 8-bit quantization, no CUDA |
| SC-001: Dataset completeness ≥95% | Phase 1: Validation | `code/utils/validators.py` | Against **GitHub API response structure** (spec-root cause; flagged for kickback) |
| SC-002: KS test p-value for goodness-of-fit | Phase 2: Distribution | `code/analyze/distributions.py` | For at least one parametric family |
| SC-003: Holm-Bonferroni adjusted p<0.05 | Phase 2: Hypothesis Testing | `code/analyze/hypothesis_tests.py` | Significant associations only when adjusted |
| SC-004: LOO-CV MAE, R² (R² [deferred] ≥0.15) | Phase 2: Mixed Effects | `code/analyze/mixed_effects.py` | From prior literature |
| SC-005: Runtime ≤6h, memory ≤7GB, no GPU | All Phases | GitHub Actions monitoring | Blocking gate for `research_complete` |

## Phase Ordering (Computational Task Order)

1. **Phase 1: Data Collection & Preprocessing** (FR-001, FR-002, FR-003)
   - Download raw API responses → `data/raw/`
   - Compute resolution times, filter invalid issues → `data/processed/`
   - **Dependency**: Must complete before any analysis phase
   - **Requirement**: ≥10 issues per repository for mixed-effects modeling

2. **Phase 2: Distribution Analysis** (FR-002, SC-002)
   - Generate ECDF plots, fit log-normal/Weibull
   - **Dependency**: Requires cleaned dataset from Phase 1

3. **Phase 3: Hypothesis Testing & Modeling** (FR-004, FR-005, SC-003, SC-004)
   - Run ANOVA/Kruskal-Wallis with Holm-Bonferroni
   - Fit mixed-effects model, LOO-CV
   - **Dependency**: Requires cleaned dataset from Phase 1

4. **Phase 4: Diagnostics & Sensitivity** (FR-006, FR-007, FR-008, SC-005)
   - Calculate VIF, flag collinearity
   - Sweep cutoffs, report threshold sensitivity (status changes)
   - Enforce associational language
   - **Dependency**: Requires results from Phase 3

5. **Phase 5: Validation & Documentation** (All SCs)
   - Validate against contract schemas
   - Generate figures for paper
   - **Dependency**: Requires all prior phases

## Risk Mitigation

| Risk | Mitigation | Contingency |
|------|------------|-------------|
| GitHub API rate limit exceeded | Exponential backoff, ≥60s wait per FR-001 | Reduce repository sample size |
| Memory overflow (>7GB) | Sample to ~7GB RAM budget, chunked processing | Further reduce issue count |
| Mixed-effects model fails to converge | Use `statsmodels` fallback, simpler random effects | Report convergence failure in results |
| Repository has <100 closed issues | Log warning, exclude from power-sensitive tests | Report as limitation in paper |
| **Repository has <10 closed issues** | **Exclude from mixed-effects modeling; log separately** | **Report as insufficient sample for random effects** |
| Programming language null | Exclude from language-group analyses | Report as missing data in SC-001 |
| Zero resolution time | Log(x+1) transform for distribution fitting | Flagged in results |

## Dependencies & Constraints

- **GitHub REST API**: Primary data source; rate-limited (High-volume authenticated requests per hour, a specified request rate per hour unauthenticated)
- **Python packages**: Pinned in `requirements.txt`; CPU-wheel compatible versions only
- **GitHub Actions**: Free-tier runner (2 CPU, 7GB RAM, 14GB disk, a predefined timeout)
- **Statistical methods**: CPU-tractable (no GPU, no 8-bit, no deep networks)

## Spec Kickback Required

The following spec items require updates to align with revised methodology:

1. **FR-007**: Currently requires "report how false-positive/false-negative rates vary" but FP/FN rates cannot be computed without ground truth in observational study. Should be updated to "report threshold sensitivity (how significance status changes across cutoffs)".

2. **SC-001**: Currently states "Dataset completeness is measured against GitHub API schema requirements" but GitHub API has no formal schema document. Should be updated to "GitHub API response structure".