# Implementation Plan: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Branch**: `001-self-compassion-feedback` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-self-compassion-feedback/spec.md`

## Summary

This feature implements a rigorous statistical pipeline to test whether self-compassion (SCS) moderates the impact of negative feedback on anxiety, rumination, and self-efficacy. The approach involves downloading a verified dataset from OSF, performing data cleaning and variable encoding (z-scoring, categorical encoding), fitting ANCOVA models with interaction terms, applying Holm-Bonferroni corrections, generating simple-slope visualizations, and producing a comprehensive HTML report. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and validated instruments, while ensuring all computations are feasible on a CPU-only CI environment.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `requests`, `jinja2`, `pyyaml`  
**Storage**: Local CSV/Parquet files (read-only raw, derived in `data/processed/`); No external database.  
**Testing**: `pytest` (unit tests for data validation, integration tests for model outputs against schema).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Data Analysis Pipeline / Statistical Research Tool.  
**Performance Goals**: Complete analysis within 6 hours; Memory usage < 7 GB; No GPU required.  
**Constraints**: CPU-only execution; No large model training; Strict adherence to FR-001 (data availability checks) and FR-016 (checksums).  
**Scale/Scope**: Single dataset (OSF); primary outcomes; A sample size of several hundred participants (estimated) will be recruited to address the research question using the established method, as outlined in prior studies (DOI:10.1234/example).; An HTML report; PNG plots.

> **Dataset Strategy Note**: The spec references an OSF URL (`https://osf.io/3k9r2/`) as a **Placeholder for Target Experimental Dataset**. This URL is **NOT** in the "Verified datasets" block. The implementation plan treats this as a critical gate: if the URL fails to fetch or the data does not contain the specific experimental variables (post-feedback anxiety, rumination, self-efficacy with feedback manipulation), the pipeline halts. No substitute is proposed because the analysis design (ANCOVA with interaction) is contingent on this specific experimental data type.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Check Status | Implementation Detail |
|-----------|--------------|-----------------------|
| **I. Reproducibility** | **PASS** | Random seed `42` enforced (FR-012); `requirements.txt` pins versions; OSF URL fixed. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to verified URLs; Dataset validity checked against spec. |
| **III. Data Hygiene** | **PASS** | SHA-256 checksum computed on download (FR-016); Raw data preserved; Derived data versioned. |
| **IV. Single Source of Truth** | **PASS** | All stats derived from `data/processed/`; No hardcoded numbers in report. |
| **V. Versioning Discipline** | **PASS** | State file updated with artifact hashes; `state/projects/...yaml` managed. |
| **VI. Validated Instruments** | **PASS** | SCS, STAI, RRS, GSES identified as validated scales; Plan checks for their presence in data. |
| **VII. Participant Well‑Being** | **PASS** | **LIMITATION ACKNOWLEDGED**: Per-record verification is impossible without raw logs. The check is strictly limited to verifying the *presence* of a compliance statement in metadata. If missing, a caveat is added. |

## Project Structure

### Documentation (this feature)

```text
specs/001-self-compassion-feedback/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── analysis_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-167-the-impact-of-self-compassion-on-resilie/
├── data/
│   ├── raw/
│   │   └── feedback_self_compassion.csv (downloaded)
│   └── processed/
│       └── clean_data.csv
├── code/
│   ├── __init__.py
│   ├── download.py          # Fetches OSF data, computes checksum, validates headers
│   ├── preprocess.py        # Cleaning, encoding, z-scoring, column mapping
│   ├── models.py            # ANCOVA fitting, VIF, Bootstrapping, Homogeneity test
│   ├── visualize.py         # Simple slope plots
│   ├── report.py            # HTML generation (Jinja2)
│   └── main.py              # Orchestration script
├── data/
│   ├── raw/                 # Downloaded CSV (read-only)
│   └── processed/           # Cleaned parquet/CSV
├── output/
│   ├── plots/               # PNG files
│   └── report.html          # Final report
├── state/
│   └── projects/PROJ-167...yaml
└── tests/
    ├── test_download.py
    ├── test_models.py
    └── test_contracts.py
```

**Structure Decision**: Single project structure chosen for simplicity and direct data flow. All analysis logic is modularized in `code/` to facilitate unit testing and reproducibility. No web server or mobile components required.

## Compute Feasibility & Methodological Rigor

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bootstrap Resampling (FR-008)** | Required for robust CIs on interaction terms. | Parametric CIs may be unreliable for small N or non-normal residuals. |
| **Holm-Bonferroni (FR-011)** | Mandatory for 3 primary outcomes to control FWER. | Simple Bonferroni is too conservative; uncorrected p-values inflate Type I error. |
| **VIF & Collinearity Checks (FR-013)** | Interaction terms often induce collinearity. | Ignoring VIF > 5 risks spurious coefficient estimates and misinterpretation. |
| **Column Mapping Logic** | Required to handle potential header variations in raw CSV. | Rigid column names risk aborting on valid data with minor naming differences. |

## Phase Breakdown

### Phase 0: Data Verification & Research (Research Complete)
- **Goal**: Confirm dataset availability, experimental design, and variable presence.
- **Steps**:
  1. **Fetch & Checksum**: Attempt to fetch `https://osf.io/3k9r2/`. Compute SHA-256 hash (FR-016).
  2. **Experimental Design Validation**: Verify metadata or data distribution confirms the presence of a feedback manipulation (e.g., distinct groups). If not, abort with `[DATA_UNAVAILABLE: Experimental design not confirmed]`.
  3. **Column Mapping & Validation**:
     - **Alias Dictionary**: Apply strict alias mapping (e.g., `scs_total` -> `scf_total`, `anxiety_post` -> `stai_post`).
     - **Ambiguity Check**: If multiple source columns map to one target, or a target has no source, abort with `[MAPPING_FAILED: Unmapped/ambiguous variables: [list]]`.
     - **Enum Validation**: Check that `feedback_cond` values match exactly `["Positive Feedback", "Neutral", "Negative Feedback"]`. Abort if mismatch.
  4. **Documentation**: Document findings in `research.md`.

### Phase 1: Data Modeling & Contracts (Data Model Complete)
- **Goal**: Define strict data schemas for input and output.
- **Steps**:
  1. Define `contracts/dataset.schema.yaml` with required columns and types.
  2. Define `contracts/analysis_result.schema.yaml` for regression outputs.
  3. **Centering Logic**: Mandate that interaction terms are constructed from *centered* variables (Z-scored SCS and Coded Feedback) to ensure orthogonality.
  4. **Covariate Logic**: Define conditional inclusion of Big Five traits (FR-018): if columns exist, include; else, log warning.
  5. **Selection Bias Warning**: If randomization is not confirmed, flag potential confounding.
  6. **Holm-Bonferroni Justification**: Document choice of Holm-Bonferroni over multivariate methods due to sample size constraints, acknowledging potential conservatism.

### Phase 2: Implementation (Code Complete)
- **Goal**: Build the analysis pipeline.
- **Steps**:
  1. Implement `download.py` with checksum verification and column mapping.
  2. Implement `preprocess.py` (listwise deletion, encoding, centering).
  3. Implement `models.py`:
     - **ANCOVA**: Fit models with `C(feedback)[T.2]:SCS_z`.
     - **Homogeneity Test (FR-019)**: Test `Covariate * Feedback` interaction.
       - **Violation Handling**: If significant (p < 0.10), **do not** use Johnson-Neyman. Instead, run **Stratified Analysis** (separate models per feedback group) or **Random Slopes Model**. Report primary interaction as "Uninterpretable under homogeneity violation" with caveat.
     - **Robustness**: VIF, Bootstrap (A substantial number of resamples will be generated.), HC3 SEs.
     - **Correction**: Apply Holm-Bonferroni separately to primary (3 outcomes) and robustness (3 outcomes) families (FR-011b).
     - **Big Five**: Conditionally include if present (FR-018).
  4. Implement `visualize.py` (Simple slopes).
  5. Implement `report.py` (HTML generation). Output must conform to `contracts/analysis_result.schema.yaml` and `contracts/analysis_output.schema.yaml`.
  6. Write `main.py` to orchestrate phases.

### Phase 3: Validation & Reporting (Research Accepted)
- **Goal**: Run full pipeline and generate artifacts.
- **Steps**:
  1. Execute `main.py` on CI.
  2. **Power Insufficient Handling (N < 92)**: If N < 92, suppress p-values and "Hypothesis Not Supported" claims. Report **only** effect sizes and confidence intervals with a "Power Insufficient" warning.
  3. Verify `report.html` renders correctly.
  4. Verify `plots/*.png` exist and contain 3 lines.
  5. Check `state/` file for hash updates.

## Risk Mitigation

- **Risk**: OSF URL `https://osf.io/3k9r2/` is not in the "Verified datasets" list.
  - **Mitigation**: The plan explicitly includes a runtime check (FR-001) that halts execution if the dataset cannot be fetched or validated. The URL is treated as a placeholder for a specific experimental design; if the design is not present, the project halts.
- **Risk**: Sample size < 92 (Power Insufficient).
  - **Mitigation**: Pipeline continues but reports **only** effect sizes and CIs, avoiding p-values to prevent Type II error misinterpretation.
- **Risk**: Non-convergence of Bootstrap (FR-008).
  - **Mitigation**: A maximum of a sufficient number of resamples will be used to ensure robust statistical inference, as determined by convergence criteria (DOI/author-year).; if not converged, report caveat instead of aborting.
- **Risk**: Homogeneity of Slopes Violation.
  - **Mitigation**: Switch to Stratified Analysis; flag primary interaction as uninterpretable.