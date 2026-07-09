# Implementation Plan: Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli

**Branch**: `001-meta-analysis-trust-deepfake` | **Date**: 2026-06-22 | **Spec**: `spec.md`

## Summary

This project implements a reproducible, automated meta-analysis pipeline to quantify the "trust bias" in deepfake facial stimuli. The system executes three core phases: (1) **Literature Ingestion & Screening**, querying OpenAlex, Semantic Scholar, and arXiv to build a candidate corpus and applying dual-reviewer logic with a *human-adjudication halt* to filter for studies measuring trust and reporting media-literacy/realism moderators; (2) **Data Harmonization**, converting heterogeneous statistical reports (means, SDs, odds ratios, t-stats) into a unified effect size metric (Cohen's d) with strict exclusion of studies with unrecoverable or reconstructed SDs from the primary pool; (3) **Meta-Analytic Modeling**, fitting random-effects models to pool effects, testing moderation by realism and media literacy (with fallback to subgroup analysis if data is sparse or heterogeneous), and generating robustness checks and publication bias diagnostics.

## Technical Context

**Language/Version**: Python (Primary) + R 4.3+ (Statistical Core).  
**Primary Dependencies**: `requests`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `rpy2` (for R integration), `metafor` (R package), `esc` (R package).  
**Storage**: Local CSV/Parquet files under `data/` (no external DB).  
**Testing**: `pytest` with mock API responses for search/screening; synthetic data for effect-size math.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM, ~14 GB disk).  
**Project Type**: Data Science Pipeline / CLI.  
**Performance Goals**: < 6 hours total runtime; < 7 GB RAM peak; < 14 GB disk usage.  
**Constraints**: 
- **No GPU**: All operations must be CPU-tractable.
- **API Rate Limits**: Search scripts must implement exponential backoff.
- **Statistical Rigor**: All p-values, CIs, and heterogeneity stats must be computed via `metafor` (via `rpy2`) or equivalent validated Python libraries.
- **SD Handling**: Strict exclusion of studies with missing/unrecoverable SDs from primary pool; conservative variance inflation for sensitivity only.
- **Adjudication**: System halts and flags for human review if Cohen's Kappa < 0.6 (satisfying FR-002).
**Scale/Scope**: Expected < 100 primary studies (based on niche topic).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Search queries and screening logic saved in `data/search_results/` and `data/screening_log.csv`. `requirements.txt` and `renv.lock` (for R) pinned. |
| **II. Verified Accuracy** | Citations are validated dynamically: DOIs from search results are resolved against Crossref/OpenAlex APIs at runtime. The "Verified datasets" block is N/A for this meta-analysis; validation is performed against the *source API metadata* (DOI, Title, Source) to ensure accuracy. Final manuscript citations will be validated against these APIs before publication. |
| **III. Data Hygiene** | Raw CSVs from APIs preserved. Derivations (effect sizes) written to new files. Checksums recorded in `state/`. No PII (only aggregate stats). |
| **IV. Single Source of Truth** | All figures (Forest, Funnel, PRISMA) generated programmatically from `data/` and `code/`. No manual transcription to paper. |
| **V. Versioning Discipline** | Content hashes for all artifacts in `state/`. `updated_at` timestamps managed by the Advancement-Evaluator. |
| **VI. Systematic Review Transparency** | `inclusion_criteria.yaml` is generated in Phase 1.1 as a machine-readable artifact. `screening_log.csv` is generated in Phase 1.3. `PRISMA_flow.pdf` is generated in Phase 4. |
| **VII. Statistical Reporting** | `metafor` (R) used for all meta-analysis. `esc` (R) for effect size conversion. Outputs extracted programmatically for the manuscript. |

## Project Structure

### Documentation (this feature)
```text
specs/001-meta-analysis-trust-deepfake/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)
```text
projects/PROJ-757-meta-analysis-of-trust-perception-in-dee/
├── code/
│   ├── 01_search_and_screen.py    # API queries, dual-reviewer logic, Kappa check, human-adjudication halt
│   ├── 02_effect_size_calc.py     # Harmonization, strict exclusion logic, p-value raw preservation
│   ├── 03_meta_analysis_driver.py # Python driver invoking 03_meta_analysis.R via rpy2
│   ├── 03_meta_analysis.R         # R script for metafor/esc (invoked by driver)
│   ├── 04_robustness_checks.py    # Sensitivity, publication bias, PDF plotting (Forest/Funnel)
│   └── utils.py                   # Logging, config, checksumming
├── data/
│   ├── search_results/            # Raw CSVs from APIs
│   ├── screening/                 # screening_log.csv, inclusion_criteria.yaml
│   ├── harmonized/                # effect_sizes.csv, moderators.csv
│   └── checksums.txt              # Artifact hashes
├── results/
│   ├── robustness/                # Sensitivity tables, Egger's test output
│   └── figures/                   # PRISMA_flow.pdf, Forest.pdf, Funnel.pdf
├── tests/
│   ├── unit/                      # Mock API tests, effect size math tests
│   └── integration/               # End-to-end pipeline tests
├── requirements.txt               # Python deps
├── renv.lock                      # R deps (if managed via renv)
└── README.md
```

**Structure Decision**: Single-project structure with distinct `code/` phases. R is used for statistical rigor (`metafor`), invoked via a Python wrapper (`03_meta_analysis_driver.py` using `rpy2`) to maintain a single Python entry point for the CI runner. This ensures compliance with the "Statistical Reporting" constitution principle while maintaining a Python-centric workflow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **R + Python Hybrid** | `metafor` and `esc` are the gold standards for meta-analysis; Python equivalents lack full feature parity for complex moderators and robustness checks. | Pure Python `statsmodels` does not support all required meta-regression diagnostics (e.g., specific Egger's test variants) with the same validated accuracy as `metafor`. |
| **Human Adjudication Halt** | FR-002 requires a "third reviewer" step when Kappa < 0.6. Automated tie-breakers introduce bias. | "Simulate third reviewer" is ambiguous and risky. We halt the pipeline and flag for human review to satisfy the spec's intent. |
| **Strict SD Exclusion** | Imputation methods introduce bias (heteroscedasticity). | Simple exclusion of all missing data would bias results, but we add a "Conservative Variance Inflation" sensitivity check to bound the error. |

## Phase Breakdown

### Phase 1: Literature Ingestion & Screening
1. **Generate `inclusion_criteria.yaml`**: Parse spec criteria into machine-readable YAML. **Output**: `data/screening/inclusion_criteria.yaml`.
2. **Search & Export**: Query OpenAlex, Semantic Scholar, arXiv. Export raw CSVs.
3. **Dual-Reviewer Simulation**: Apply inclusion criteria to abstracts. Calculate Cohen's Kappa.
4. **Adjudication Logic (FR-002)**:
   - **If** Cohen's Kappa >= 0.6: Proceed.
   - **If** Cohen's Kappa < 0.6: **HALT** pipeline. Flag disputed studies in `screening_log.csv` with `adjudication_required=True`. Log error: "Human Adjudication Required (Kappa < 0.6)".
5. **Output**: `data/screening/screening_log.csv`, `data/search_results/raw_studies.csv`.

### Phase 2: Data Harmonization
1. **Extract Statistics**: Parse means, SDs, t-stats, p-values. **Preserve** raw p-value strings (e.g., "p < 0.05") in `p_value_raw`.
2. **SD Handling (Strict Exclusion)**:
   - If SD is present: Use directly.
   - If SD missing but exact t-stat or exact p-value present: Reconstruct SD. Set `sd_reconstructed=True`. **Exclude** from primary pool (`included_in_primary=False`).
   - If SD missing and only rounded p-value (e.g., "p < 0.05") present: **Exclude** from primary pool (`included_in_primary=False`). Set `p_value_is_inexact=True`.
   - If SD missing and no reconstruction possible: **Exclude** from primary pool (`included_in_primary=False`).
   - **No Imputation**: Do NOT impute mean SD.
3. **Effect Size Calculation**: Convert to Cohen's d.
4. **Output**: `data/harmonized/effect_sizes.csv` with flags (`sd_imputed`, `sd_reconstructed`, `included_in_primary`).

### Phase 3: Meta-Analytic Modeling
1. **Power Check**: Count studies with valid moderator data (k).
   - **If** k < 10: **Switch** to Subgroup Meta-Analysis (if discretizable) or report "Insufficient Power".
2. **Realism Harmonization**:
   - If `realism_level` is continuous (e.g., FID, detection rate): Proceed to Meta-Regression.
   - If `realism_level` is categorical (High/Low) or heterogeneous: **Switch** to Subgroup Meta-Analysis.
3. **Moderator Handling**:
   - If `media_literacy_score` is categorical (High/Low), set to `NaN` for regression.
4. **Primary Pool**: Fit Random-Effects Model on studies with `included_in_primary=True`.
5. **Output**: `results/analysis_output.csv`, `results/robustness/sensitivity_analysis.csv`.

### Phase 4: Robustness & Reporting
1. **Sensitivity Analysis**:
   - Leave-one-out.
   - **Exclude** all studies with `sd_reconstructed=True` (even if they were in primary pool) to verify robustness.
   - **Conservative Variance Inflation**: Run a sensitivity analysis replacing missing SDs with the **maximum observed SD** in the dataset to bound the potential effect.
2. **Publication Bias**: Egger's test, Funnel Plot.
3. **Plot Generation**: Generate `Forest.pdf` and `Funnel.pdf` with **labeled axes** and **visible confidence intervals**.
4. **Validation**: Verify `Forest.pdf` and `Funnel.pdf` exist and contain labeled axes and visible CIs.
5. **Output**: `results/figures/Forest.pdf`, `results/figures/Funnel.pdf`, `results/figures/PRISMA_flow.pdf`.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| **Zero Studies** | If search yields < 3 studies, report as "Insufficient Data" and halt. |
| **API Rate Limits** | Implement exponential backoff and caching. |
| **Non-Convergence** | Fallback to fixed-effects model; log reason. |
| **Low Power for Moderators** | Fallback to Subgroup Meta-Analysis; report as exploratory. |
| **Missing SDs** | Exclude from primary pool; run conservative sensitivity check (max SD). |
| **Ecological Fallacy** | Explicitly frame results as study-level associations; use subgroup analysis as robustness check. |
| **Human Adjudication Required** | Pipeline halts and flags for human review if Kappa < 0.6. |

## Decision Rationale

**Why Human Adjudication Halt?**
FR-002 requires a "third reviewer" step. Automated tie-breakers introduce bias and violate the spec's intent. We halt the pipeline and flag for human review to ensure quality control.

**Why Strict SD Exclusion?**
Imputing SDs based on sample size introduces bias (heteroscedasticity). We exclude these studies from the primary estimate to preserve validity. A conservative sensitivity analysis (using max observed SD) bounds the potential error.

**Why R for Meta-Analysis?**
`metafor` is the industry standard. We invoke it via `rpy2` from `03_meta_analysis_driver.py` to maintain a single Python entry point for the CI runner.

**Why Subgroup Fallback?**
If continuous realism metrics are unavailable for >30% of studies, a regression is invalid. Switching to Subgroup Meta-Analysis allows us to answer the research question for the full dataset using categorical comparisons.