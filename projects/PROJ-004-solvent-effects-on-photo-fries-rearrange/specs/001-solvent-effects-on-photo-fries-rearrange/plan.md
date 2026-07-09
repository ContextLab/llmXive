# Implementation Plan: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Branch**: `001-solvent-effects` | **Date**: 2026-05-17 | **Spec**: `specs/001-solvent-effects/spec.md`
**Input**: Feature specification from `/specs/001-solvent-effects/spec.md`

## Summary

This feature implements a computational-experimental pipeline to quantify the *associational* relationship between solvent polarity and singlet-radical-pair intermediate lifetimes in the Photo-Fries rearrangement of phenyl benzoate. The system configures a solvent series (non-polar to polar), processes simulated (or uploaded) transient-absorption data to extract lifetimes via **Joint Non-Linear Mixed-Effects (NLME) modeling**, computes solvation energies using DFT (B3LYP/6-31G*), and performs statistical correlation using a **Bayesian Hierarchical Model** with a PCA-derived "Solvent Polarity Index" to avoid tautology. The implementation strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and CPU-only feasibility on GitHub Actions free-tier runners.

**Key Methodological Corrections**:
-   **Causal Framing**: All claims are strictly framed as *associational*. The study design cannot control for confounders (viscosity, specific interactions), so no causal mechanisms are inferred.
-   **Statistical Rigor**: Replaced standard ANOVA/Regression with Bayesian Hierarchical Modeling (BHM) and NLME to handle low N (n=3) and propagate uncertainty from kinetic fitting into the regression. **Exact posterior probabilities (p-value equivalents) and multiple-comparison correction (Bonferroni/Holm) will be reported.**
-   **Collinearity**: Primary analysis uses a single PCA-derived "Solvent Polarity Index". Separate univariate models for dielectric constant and solvation energy are forbidden for hypothesis testing due to physical coupling (tautology).
-   **Circularity**: Simulation of lifetimes uses an independent empirical model (Arrhenius with randomized activation energy), distinct from the DFT solvation energy model (Born equation), ensuring non-circular validation.
-   **Product Distribution**: Explicitly labeled as a *derived artifact* of the lifetime model, not an independent validation target. **No NMR methods are used; HPLC-UV is the only product analysis method.**
-   **Exploratory Framing**: The study is explicitly framed as **exploratory** and **hypothesis-generating** due to the low sample size (n=3). While Bayesian methods allow for uncertainty propagation, the low power is a limitation that prevents definitive causal claims. The power analysis is documented to transparently report this limitation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `scikit-learn`, `statsmodels`, `pymc` (for Bayesian/NLME), `pyyaml`, `h5py`, `rdkit`.  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/compute/`) with checksums recorded in `state/`.  
**Testing**: `pytest` (unit tests for kinetic fitting, integration tests for pipeline flow, contract tests for schema validation).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Scientific Data Pipeline / Analysis Library.  
**Performance Goals**: Complete full pipeline (simulation -> NLME fitting -> Bayesian stats) for 5 solvents with 3 replicates each within 4 hours.  
**Constraints**: No GPU usage; no large LLM inference; Data subsets must fit in available RAM.; all statistical claims must be framed as associational.  
**Scale/Scope**: Multiple solvent conditions, multiple replicates each (resulting in multiple kinetic traces), multiple solvation energy calculations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Random seeds pinned in `code/`. `requirements.txt` pins all versions. Pipeline runs end-to-end on fresh runner. |
| **II. Verified Accuracy** | **COMPLIANT** | All citations in `research.md` and `paper/` will be validated by `Reference-Validator` against primary sources (arXiv URLs provided in spec). |
| **III. Data Hygiene** | **COMPLIANT** | All files in `data/` checksummed in `state/`. Raw data immutable; derivations create new files. No PII. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures/stats trace to `data/processed/` rows. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes tracked for all artifacts. `state/` updated on change. |
| **VI. Comp-Exp Consistency** | **COMPLIANT** | DFT and Kinetic units standardized (kcal/mol, ns). Deviation analysis logged in `docs/deviation_analysis.md`. |
| **VII. Chemical Provenance** | **COMPLIANT** | Solvent/Reagent logs (manufacturer, lot, purity) stored in `data/chemicals/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-solvent-effects/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/
├── data/
│   ├── raw/                  # Simulated transient-absorption CSVs, DFT input files, or uploaded real data
│   ├── processed/            # Fitted lifetimes, solvation energies, statistical outputs
│   └── chemicals/            # Solvent lookup tables (versioned)
├── code/
│   ├── __init__.py
│   ├── config.py             # Random seeds, paths, constants
│   ├── simulate_data.py      # Generates synthetic decay traces (US-1) using independent Arrhenius model
│   ├── fit_kinetics.py       # Joint NLME fitting (US-2)
│   ├── compute_solvation.py  # Wraps DFT logic or loads pre-computed (US-3)
│   ├── analyze_stats.py      # Bayesian Hierarchical Model, PCA, Sensitivity (US-3)
│   └── main.py               # Orchestration script
├── tests/
│   ├── contract/             # Schema validation tests
│   ├── integration/          # Full pipeline flow tests
│   └── unit/                 # Fitting, stats logic tests
├── docs/
│   └── deviation_analysis.md # DFT vs Exp comparison
└── state/
    └── projects/PROJ-004-solvent-effects-on-photo-fries-rearrange.yaml
```

**Structure Decision**: Single project structure selected to minimize overhead for a focused scientific analysis pipeline. All data and code reside within the project directory to satisfy "Single Source of Truth" and "Reproducibility" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separate `compute/` and `raw/`** | Required by Constitution Principle III (Data Hygiene) to distinguish raw instrument output from derived data. | Merging would violate "no modification in place" rule. |
| **Simulated Data Generator** | Real instrument data is unavailable for CI; simulation allows deterministic testing of the pipeline logic (US-1, US-2). | Using external real data would break reproducibility on fresh runners without manual upload. |
| **VIF Diagnostics** | Required by SC-009 to address collinearity between dielectric constant and solvation energy. | Simple regression would fail to distinguish independent effects, violating methodological rigor. |
| **Bayesian Hierarchical Modeling** | Required to handle low N (n=3) and propagate uncertainty from kinetic fitting into regression. | Standard ANOVA/Regression provides insufficient power and ignores first-stage uncertainty. |
| **PCA Composite Metric** | Required to avoid tautology between dielectric constant and solvation energy. | Separate univariate models are physically unsound due to variable coupling. |

## Unresolved Panel Concerns Resolution

The following concerns from the previous iteration have been resolved in this plan:

1.  **T039 (Full pipeline integration test) Ordering**: The execution logic in `main.py` is strictly ordered: Phase 0 (Data Sim/Load) -> Phase 1 (Kinetic Fit) -> Phase 2 (Solvation Calc) -> Phase 3 (Statistical Analysis) -> Phase 4 (Integration Test). T039 now explicitly depends on the successful completion of Phase 5 (T034) and Phase 4 (T026) outputs, ensuring data availability before validation. The integration test runs **after** all statistical outputs are generated.
2.  **T015 (Real vs Simulated Data)**: The plan now includes a mechanism to ingest real data. `quickstart.md` provides a mechanism to replace simulated data with real CSV files in `data/raw/` (naming convention `trace_<solvent>_<replicate>.csv`). The system validates these files against the schema before processing. The default CI path uses simulation, but the code supports real data via file upload.
3.  **T030b (ANOVA & P-values)**: The plan explicitly **reverses** the previous "avoid p-value" stance. Phase 3 (`analyze_stats.py`) implements Bayesian Hierarchical Modeling with exact posterior probabilities (p-value equivalents) and multiple-comparison correction (Bonferroni/Holm) as required by SC-003 and US-3. The low N (n=3) is addressed via Bayesian shrinkage and effect size reporting with wide credible intervals.
4.  **T042 (NMR vs HPLC)**: The plan strictly adheres to the spec. **NMR is removed**. Product distribution analysis (if included) will use the HPLC-UV proxy data generated in the simulation, consistent with US-3 and the Assumptions section. No unverified instrument capabilities are introduced.

## Statistical Rigor & Feasibility Notes

-   **Statistical Rigor**: The plan uses a **Joint Non-Linear Mixed-Effects (NLME)** model to simultaneously fit kinetics and solvent effects, avoiding the bias of two-stage estimation. A **Bayesian Hierarchical Model** is used for the final correlation analysis to handle low N. The primary predictor is a **PCA-derived Solvent Polarity Index** to avoid tautology between dielectric constant and solvation energy. Separate univariate models are **forbidden** for hypothesis testing.
-   **Compute Feasibility**: All methods (`pymc`, `statsmodels`, `scipy`) are CPU-tractable. No GPU libraries are used. The dataset size (15 traces, small DFT inputs) fits easily within 7 GB RAM.
-   **Dataset Variable Fit**: The simulation generates exactly the variables required: `time`, `absorbance`, `solvent_id`, `dielectric_constant`, `temperature`. No external variable mismatch is possible as the data is generated to match the spec. The simulation model (Arrhenius) is explicitly independent of the DFT model (Born) to prevent circularity.
-   **Confounding Variables**: The plan explicitly acknowledges that viscosity and specific solute-solvent interactions are uncontrolled confounders. The study design cannot distinguish direct solvent effects from these confounders. All findings are framed as *associational* only.
-   **Product Distribution**: Product distribution is a *derived artifact* of the lifetime model (via cage effect) and is not an independent validation target. It is retained only as a secondary consistency check.
-   **Power & Exploratory Framing**: The study is explicitly framed as **exploratory** and **hypothesis-generating** due to the low sample size (n=3). While Bayesian methods allow for uncertainty propagation, the low power is a limitation that prevents definitive causal claims. The power analysis is documented to transparently report this limitation.
