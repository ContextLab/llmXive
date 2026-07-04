# Implementation Plan: Simulation-Based Sensitivity Analysis of Framing Effects on Perceived Severity of Online Misinformation

**Branch**: `001-the-impact-of-framing` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-framing/spec.md`

## Summary

This project implements a **simulation-based sensitivity analysis** to evaluate the statistical power of a hypothetical experiment comparing "harm-framed" versus "fact-framed" misinformation. The system uses the MPSD dataset (or a verified proxy) strictly as a source of realistic stimulus parameters (headlines, domains) to generate a synthetic response dataset. 

**Design Clarification**: The simulation uses a **between-subjects design** with **N=300 total participants** (150 per condition), sampled across **10 unique stimuli** (15 participants per stimulus per condition). This exact N aligns with the *a priori* power analysis target. The analysis does not merely test a single generated effect; it performs a **sensitivity analysis** by varying the input effect size (delta) across multiple simulation runs to map the relationship between true effect size and statistical detection probability. This transforms the study from a tautological check into a valid assessment of experimental design sensitivity.

The system fits a mixed-effects linear model (severity) and a logistic regression model (sharing intention) to test the framing effect, applying Bonferroni corrections and reporting effect sizes. The pipeline includes an *a priori* power analysis using the R `pwr` package to validate sample size adequacy.

## Technical Context

**Language/Version**: R 4.3+ (Required to satisfy Spec FR-003 and FR-007)  
**Primary Dependencies**: `lme4`, `lmerTest`, `pwr`, `dplyr`, `ggplot2`, `tidyr`, `data.table`  
**Storage**: Local CSV/Parquet files in `data/` and `results/`  
**Testing**: `testthat` (unit tests for data generation logic, statistical calculation verification)  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, No GPU)  
**Project Type**: Data Analysis / Simulation Pipeline  
**Performance Goals**: Complete analysis in < 15 minutes; Memory usage < 2GB during peak processing.  
**Constraints**: No GPU usage; synthetic data generation must be deterministic (seeded); all external data fetches must be idempotent and checksummed.  
**Scale/Scope**: Synthetic dataset N=300; 10 unique stimuli.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; dataset fetch URLs verified; `requirements.txt` (renamed to `DESCRIPTION`/`renv.lock` or `requirements.txt` for R) pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations for MPSD methodology and statistical methods (Cohen's d, Bonferroni) will be validated against primary sources. No fabricated dataset URLs used. If no verified source with headlines exists, synthetic generation is used. |
| **III. Data Hygiene** | **PASS** | Raw stimulus data (if downloaded) and generated synthetic data will be checksummed. No in-place modification of raw files. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `results.md` will be programmatically derived from `data/` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state file updated on artifact change. |
| **VI. Framing Condition Consistency** | **PASS** | Synthetic data generation script will explicitly create `harm` and `fact` variants as per spec, logging the exact wording logic. |
| **VII. Outcome Measurement Integrity** | **PASS** | Severity and Sharing (binary) scales will be strictly enforced in synthetic generation; analysis scripts will reference these columns directly. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-framing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── synthetic_dataset.schema.yaml
    └── analysis_results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-399-the-impact-of-framing-on-perceived-sever/
├── code/
│   ├── DESCRIPTION          # R package metadata
│   ├── NAMESPACE            # R exports
│   ├── 01_data_prep.R       # Fetch/validate stimulus data, generate synthetic responses
│   ├── 02_power_analysis.R  # A priori power calculation (pwr package)
│   ├── 03_analysis.R        # Mixed-effects & Logistic regression (lme4)
│   └── 04_export.R          # Generate results.md and plots
├── data/
│   ├── raw/                     # Source stimulus data (if any)
│   └── processed/               # Synthetic dataset (CSV)
├── results/
│   ├── plots/                   # Bar plots, interaction plots, sensitivity curves
│   └── results.md               # Final report
└── tests/
    ├── test_data_generation.R
    └── test_statistics.R
```

**Structure Decision**: Single-project R structure selected. The analysis requires `lme4` and `pwr` as mandated by the spec (FR-003, FR-007). Python alternatives were rejected to ensure strict compliance with functional requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Mixed-Effects Model (R/lme4)** | Required by Spec FR-003 to account for stimulus-level variance (random intercepts) and to use the mandated R stack. | Python `statsmodels` was considered but rejected to satisfy the explicit `lme4` requirement in the spec. |
| **Synthetic Data Generation** | Required by Assumption 1; the real MPSD-v2 lacks the `framing_condition` variable. | Using real data directly is impossible as the variable does not exist; simulation is the only valid approach for this hypothesis. |
| **Bonferroni Correction** | Required by FR-004 to control family-wise error rate. | Uncorrected p-values would be statistically invalid for multiple hypothesis testing. |
| **Sensitivity Analysis (Varying Delta)** | Required to avoid tautology. The study maps power vs. effect size, not just a single test. | A single-effect simulation would be a self-verification loop with no scientific insight. |

## Computational Feasibility & Methodological Rigor

### Compute Feasibility
- **Dataset Size**: Synthetic N=300 is trivial for RAM/CPU.
- **Libraries**: `lme4`, `pwr`, `dplyr` are fully compatible with GitHub Actions free tier (CPU-only).
- **Runtime**: Power analysis, data generation, and model fitting for N=300 will complete in < 5 minutes.

### Methodological Rigor
- **FR/SC Coverage**:
  - **FR-001/SC-001**: Data validation and Mixed-Effects model implementation (R `lme4`).
  - **FR-002/SC-002**: Synthetic generation logic and Cohen's d calculation.
  - **FR-003/SC-003**: Logistic regression implementation (R `glm`).
  - **FR-004**: Bonferroni correction logic explicitly coded.
  - **FR-005/SC-004**: Power analysis implementation (R `pwr`).
  - **FR-006/007/008**: Effect size, visualization, and export logic.
- **Statistical Rigor**:
  - **Multiple Comparisons**: Bonferroni correction applied as per FR-004.
  - **Power**: *A priori* power analysis (FR-007) ensures N=300 is sufficient for d=0.3.
  - **Causal Claims**: The plan explicitly frames results as "potential causal effects" from a simulated experiment (random assignment), avoiding over-claiming on observational data.
  - **Collinearity**: `framing_condition` is an independent experimental variable; `content_domain` is a control. No definitional collinearity exists.
  - **Sensitivity Analysis**: The study varies the input effect size (delta) to map detection probability, avoiding the tautology of testing a fixed generated effect.
- **Dataset-Variable Fit**:
  - **MPSD-v2 / Proxy**: Used *only* for stimulus parameters (headlines, domains). The plan acknowledges that `framing_condition` is **not** in the source data and is generated synthetically. If no verified source with headlines exists, synthetic headlines are generated.