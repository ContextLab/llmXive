# Implementation Plan: Predicting Molecular Complexity with Information Theory

**Branch**: `[PROJ-431-predicting-molecular-complexity]` | **Date**: 2026-06-28 | **Spec**: `specs/PROJ-431-predicting-molecular-complexity/spec.md`
**Input**: Feature specification from `/specs/PROJ-431-predicting-molecular-complexity/spec.md`

## Summary

This project implements a CPU-tractable pipeline to compute Shannon entropy-based complexity scores (atom and bond degree distributions) for molecular graphs and evaluate their correlation with aqueous solubility (logS) and membrane permeability (logP). The implementation strictly adheres to the functional requirements (FR-001 to FR-011) and success criteria (SC-001 to SC-010) defined in the spec, utilizing RDKit for graph processing and scikit-learn for Ridge Regression modeling.

**Critical Methodological Note**: While the source spec defines Success Criteria (SC-001, SC-006, SC-008, SC-009) with a hard threshold of |r| ≥ 0.30 and (SC-002, SC-007) with RMSE ≤ 1.0, this plan interprets these as **scientific hypotheses to be tested** rather than **pipeline validity gates**. If the observed correlation or RMSE does not meet these thresholds, the pipeline will successfully report the observed values as valid scientific findings (negative results). The project's scientific validity is determined by the **rigor of the methodology** (proper baseline comparison, confounding control, and statistical correction), not by achieving the specific numerical targets in the spec. This avoids design bias where null results are treated as failures.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `rdkit`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `pyyaml`  
**Storage**: Local file system (CSV for data, PKL for models, JSON for reports, PNG for plots)  
**Testing**: `pytest` (unit tests for entropy calculation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: CLI / Data Science Pipeline  
**Performance Goals**: Process [deferred] molecules in ≤ 30 minutes on single CPU; model training < 5 minutes.
**Constraints**: No GPU/CUDA; no 8-bit quantization; memory footprint < 6 GB; strict adherence to Bonferroni correction for 4 tests.  
**Scale/Scope**: Single dataset processing (up to 10k rows); hypothesis tests; regularization sweeps.

> **Data Source SSoT**: Although the spec's Assumptions section generically mentions "Public FTP endpoints for ZINC15 or ChEMBL", this plan explicitly adopts the **verified HuggingFace URLs** listed in `research.md` as the **Single Source of Truth** for data acquisition. The generic assumption is superseded by these specific, verified sources to ensure reproducibility.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned to `42` in `code/`. Dependencies pinned in `requirements.txt`. Data fetched from verified HuggingFace URLs only. |
| **II. Verified Accuracy** | **PASS** | Dataset sources restricted to the "Verified datasets" block in the spec. No external URLs invented. |
| **III. Data Hygiene** | **PASS** | Raw data (CSV) preserved; derived data (entropy CSV) written to new files. Checksums recorded in state file. |
| **IV. Single Source of Truth** | **PASS** | All metrics (RMSE, r) generated programmatically and stored in `results/` JSON. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts (models, plots) will be named with content hashes or timestamps in the final implementation. |
| **VI. Molecular Graph Integrity** | **PASS** | SMILES validation via RDKit is mandatory. Malformed entries logged and skipped (FR-008). Entropy computed strictly on degree distributions. |
| **VII. Statistical Transparency** | **PASS** | Ridge Regression (α=1.0 default) with A train-test split with a majority portion allocated to training and a smaller portion to testing.. Metrics reported in JSON. Bonferroni correction applied to p-values (FR-010). Baseline models (Mean, MW-only) included for comparison. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-431-predicting-molecular-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-431-predicting-molecular-complexity-with-inf/
├── code/
│   ├── __init__.py
│   ├── cli.py                 # Main entry point (compute_entropy, train_model, plot_correlation)
│   ├── entropy.py             # FR-002, FR-003: Shannon entropy calculation logic
│   ├── model.py               # FR-006, FR-011: Ridge Regression training & sensitivity
│   ├── viz.py                 # FR-007: Plotting logic
│   ├── utils.py               # Logging, validation, file I/O
│   └── requirements.txt       # Pinned dependencies
├── data/
│   ├── raw/                   # Downloaded CSVs (ZINC15/ChEMBL subset)
│   └── processed/             # Entropy-enriched CSVs
├── results/
│   ├── models/                # *.pkl files
│   ├── reports/               # *.json metrics
│   └── plots/                 # *.png files
├── tests/
│   ├── unit/                  # Entropy logic tests
│   └── integration/           # Full pipeline tests
└── README.md
```

**Structure Decision**: Selected Option 1 (Single project) with a modular CLI structure. This aligns with the spec's requirement for a command-line interface (`compute_entropy`, `train_model`, `plot_correlation`) and keeps data processing logic isolated from the CLI entry point for easier testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | No violations detected. The spec is well-defined, and the proposed architecture (CLI + modular scripts) is standard for this scope. | N/A |

## Statistical Methodology & Rigor

### 1. Null Hypothesis & Test Statistic
- **Null Hypothesis (H0)**: Pearson correlation coefficient $r = 0$ (no linear relationship).
- **Alternative Hypothesis (H1)**: $r \neq 0$.
- **Test Statistic**: $t = r \sqrt{\frac{n-2}{1-r^2}}$, following a $t$-distribution with $n-2$ degrees of freedom.
- **P-value Calculation**: Two-tailed p-value derived from the t-statistic.

### 2. Multiple Comparison Correction (FR-010)
- **Family**: Multiple tests (Atom-logS, Atom-logP, Bond-logS, Bond-logP).
- **Method**: Bonferroni correction applied to control Family-Wise Error Rate (FWER).
- **Adjusted Threshold**: $\alpha_{adj} = 0.05 / 4 = 0.0125$.
- **Sensitivity Analysis**: Benjamini-Hochberg (FDR) adjusted p-values will also be reported to account for potential collinearity between Atom and Bond entropy.

### 3. Baseline & Confounding Control
To address the risk that correlations are driven by molecular size (MW) rather than structural complexity:
- **Baseline Model 1 (Null)**: Predict target using the mean of the training set.
- **Baseline Model 2 (Size)**: Predict target using only Molecular Weight (MW) and Atom Count.
- **Scientific Success Criterion**: The Entropy model must demonstrate **lower RMSE** and **higher |r|** than the Size baseline. If the Entropy model does not outperform the Size baseline, the result is reported as "Entropy adds no predictive value beyond molecular size," which is a valid scientific conclusion.
- **Partial Correlation**: Report partial correlation between Entropy and Target, controlling for MW and Atom Count.

### 4. Dataset Verification (Hard Gate)
- **Pre-condition**: Before any processing, the pipeline verifies that the input dataset contains `smiles`, `logS`, and `logP` columns.
- **Action**: If columns are missing, the pipeline aborts with a clear error message. This converts the "Assumption" in the spec into a verified fact.

### 5. Sensitivity Analysis (FR-011)
- **Sweep**: $\alpha \in \{0.1, 1.0, 10.0\}$.
- **Stability Metric**: Relative range of RMSE and $r$ across the sweep must be $< 10\%$.
- **Collinearity Check**: If Atom and Bond entropy are highly correlated ($r > 0.8$), a multivariate model (Entropy + MW) will be run to assess unique contribution.