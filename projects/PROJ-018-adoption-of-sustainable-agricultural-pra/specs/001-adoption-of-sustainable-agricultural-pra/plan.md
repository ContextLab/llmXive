# Implementation Plan: Adoption of Sustainable Agricultural Practices in Low‑Income Areas through Community Engagement

**Branch**: `018-adoption-sustainable-agriculture` | **Date**: 2026-06-24 | **Spec**: `specs/018-adoption-sustainable-agriculture/spec.md`
**Input**: Feature specification from `/specs/018-adoption-sustainable-agriculture/spec.md`

## Summary

This feature implements a reproducible statistical pipeline to investigate factors influencing the adoption of sustainable agricultural practices in low-income communities, with a focus on the mediating role of community engagement. The technical approach uses logistic regression and mediation analysis on agricultural survey data. Due to the absence of verified URLs for World Bank LSMS or FAO FIES microdata in the project's verified dataset block, the CI pipeline will utilize a synthetic data generator conforming to the required schema to ensure reproducibility and feasibility on free-tier CPU runners, while documenting the data gap for manual research execution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, statsmodels, scikit-learn, matplotlib, pyyaml, factor_analyzer  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: pytest  
**Target Platform**: Linux server (GitHub Actions free-tier)  
**Project Type**: data-analysis-pipeline  
**Performance Goals**: < 6 hours runtime, < 7 GB RAM usage  
**Constraints**: CPU-only, no GPU, reproducible seeds, no external API reliance for CI (synthetic fallback)  
**Scale/Scope**: ~10k synthetic records for CI; real data ingestion manual step  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; synthetic data generator ensures CI reproducibility. |
| **II. Verified Accuracy** | PASS | Citations restricted to verified dataset block (see `research.md`); data gaps documented. |
| **III. Data Hygiene** | PASS | Raw data immutable; derivations produce new files; checksums recorded in `state/`. |
| **IV. Single Source of Truth** | PASS | All stats trace to `data/` and `code/`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Content hashes tracked; `updated_at` timestamps updated on artifact changes. |
| **VI. Survey Data Provenance** | PASS | Metadata recorded in `data/metadata.yaml`; raw files preserved if downloaded manually. |
| **VII. Statistical Modeling Transparency** | PASS | Model defined in `code/`; choices logged in `modeling_log.yaml`; results saved to `results/`. |

## Project Structure

### Documentation (this feature)

```text
specs/018-adoption-sustainable-agriculture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-018-adoption-of-sustainable-agricultural-pra/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_download_data.py
│   ├── 02_clean_data.py
│   ├── 03_engineer_features.py
│   ├── 04_model_analysis.py
│   └── 05_generate_report.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata.yaml
├── results/
│   ├── figures/
│   └── tables/
└── tests/
    ├── test_pipeline.py
    └── test_schemas.py
```

**Structure Decision**: Single project structure (`projects/PROJ-018...`) to keep data and code tightly coupled for reproducibility (Constitution Principle I). Scripts are ordered to ensure data download precedes cleaning, which precedes modeling (Computational Task Ordering).

## Phase Breakdown & Requirement Mapping

### Phase 0: Data Acquisition & Verification
- **FR-001**: Implement `01_download_data.py`. *Constraint*: If verified URL for LSMS/FAO is missing, use synthetic generator with schema validation.
- **FR-002**: Validate variables (age, education, farm_size, credit, adoption, engagement). Log gaps. **See contracts/dataset.schema.yaml** for variable requirements and validation rules.
- **SC-001**: Verify ≥ 95% required variables present in raw dataset (or synthetic equivalent).
- **Constitution VI**: Record source metadata in `data/metadata.yaml`.

### Phase 1: Data Cleaning & Preprocessing
- **FR-003**: Impute/remove missing values; normalize categorical codes; export cleaned CSV.
- **Edge Case**: Exclude records with > 30% missing values; log count.
- **Constitution III**: Preserve raw data; write derivations to new files.

### Phase 2: Feature Engineering
- **FR-004**: Compute `engagement_score` from proxy items (membership, extension, collective action, knowledge exchange). Report Cronbach's α **and conduct exploratory factor analysis (EFA) to assess construct validity**. If α < 0.70, document limitation and note that reliability does not guarantee validity.
- **FR-005**: Create `adoption_binary` (1 if any sustainable practice reported).
- **FR-011**: Use weighted sum for engagement score; flag if < 3 proxies available. **Include convergent validity check (correlation with theoretically related constructs) as additional validity evidence**.
- **SC-002**: Report Cronbach's α; document limitation if < 0.70. **Report EFA factor loadings and convergent validity correlations**.
- **US-2**: Independent test passes if columns generated and stats reported.

### Phase 3: Statistical Modeling
- **FR-006**: Fit logistic regression (`adoption_binary` ~ `engagement_score` + covariates).
- **FR-007**: Calculate VIF for all predictors; flag VIF ≥ 5. **Additionally compute correlation matrix for all predictors to detect non-linear and complex multicollinearity patterns. Perform principal component analysis (PCA) if correlation matrix indicates potential issues (pairwise correlations > 0.70)**.
- **FR-008**: Apply Benjamini-Hochberg FDR (q ≤ 0.10); report adjusted p-values.
- **FR-009**: Compute ROC/AUC.
- **FR-012**: Perform mediation analysis (Baron & Kenny + bootstrap CI ≥ 1000 resamples). **Explicitly document limitations: Baron & Kenny approach in observational data cannot establish causality due to potential unobserved confounders. Conduct sensitivity analysis using E-values and Rosenbaum bounds to assess robustness of mediation effects to unmeasured confounding in the mediator-outcome relationship**. **Minimum sample size: ≥500 observations required for stable bootstrap indirect effect estimates in mediation analysis**. **See contracts/results.schema.yaml** for output validation requirements.
- **SC-003**: Report AUC (null results documented).
- **SC-004**: Ensure VIF < 5 (or document collinearity).
- **SC-005**: Report FDR results (significant or null).
- **SC-006**: Power analysis (Adequate events per predictor for logistic regression; ≥500 observations for mediation bootstrap stability). Document shortfall if applicable. **Mediation analysis requires larger samples than basic logistic regression; if N < 500, document power limitation for indirect effect estimates**.
- **Statistical Rigor**: Address causality assumptions (observational data); no causal claims.

### Phase 4: Reporting
- **FR-010**: Generate PDF report (descriptives, regression table, VIF, ROC, interpretation, mediation, sensitivity analysis).
- **Constitution IV**: All figures/tables trace to `code/` and `data/`.
- **Constitution VII**: Save `modeling_log.yaml` with random seeds and choices.

## Compute Feasibility

- **Runtime**: Estimated < 2 hours on 2 CPU, 7 GB RAM (pandas/statsmodels are CPU-efficient).
- **Memory**: Data subset to ~10k rows for CI; fits within 7 GB.
- **Disk**: < 1 GB total (CSV/Parquet).
- **Libraries**: `pandas`, `statsmodels`, `scikit-learn`, `matplotlib`, `factor_analyzer` (all CPU-compatible).
- **No GPU**: No CUDA/torch dependencies.