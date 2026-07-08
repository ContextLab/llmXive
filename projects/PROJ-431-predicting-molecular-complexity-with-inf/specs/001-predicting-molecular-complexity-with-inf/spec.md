# Feature Specification: Predicting Molecular Complexity with Information Theory

**Feature Branch**: `[PROJ-431-predicting-molecular-complexity]`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Complexity with Information Theory – evaluate how information‑theoretic descriptors of molecular graphs correlate with solubility and membrane permeability."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Information‑Theoretic Complexity Scores (Priority: P1)

A researcher wants to generate entropy‑based complexity scores for a curated set of molecules so that the scores can be used as features in downstream analyses.

**Why this priority**: Without the core scores, no further modelling or interpretation is possible; this is the fundamental data product of the project.

**Independent Test**: Provide a CSV containing a representative set of SMILES strings; run the pipeline and verify that a new CSV with two additional columns (`atom_entropy`, `bond_entropy`) is produced, each containing numeric values for every input molecule.

**Acceptance Scenarios**:

1. **Given** a valid CSV file with a `smiles` column, **When** the user executes the `compute_entropy` command, **Then** the system outputs a CSV with the original columns plus `atom_entropy` and `bond_entropy` for each row **and** SC‑005 (see Success Criteria) is satisfied.
2. **Given** a CSV where some SMILES strings are malformed, **When** the command runs, **Then** the system logs a warning for each malformed entry and skips them, leaving the rest of the output intact.
3. **Given** a CSV containing **10 000** valid molecules, **When** the `compute_entropy` command is executed on a single‑CPU machine, **Then** the processing completes within **30 minutes**, satisfying **SC‑003**.

---

### User Story 2 – Train & Evaluate Ridge Regression Models (Priority: P2)

A chemoinformatics analyst wants to assess whether the entropy scores predict aqueous solubility (logS) and octanol‑water partition coefficient (logP) using a simple regression model. **logP is employed as a widely accepted proxy for membrane permeability**, reflecting the compound's ability to cross lipid bilayers. The system tests for a significant correlation (|r| ≥ 0.30), hypothesizing that higher structural complexity may correlate with lower solubility.

**Why this priority**: This story validates the scientific hypothesis and produces the quantitative results required for the project’s expected outcomes.

**Independent Test**: Using the output CSV from Story 1 (including `logS` and `logP` columns), run the `train_model` script and confirm that a model file is saved and a JSON report containing RMSE and Pearson r for each property is generated.

**Acceptance Scenarios**:

1. **Given** a dataset split 80/20 (train/test), **When** the analyst runs `train_model --target logS`, **Then** the system trains a Ridge Regression model, saves `ridge_logS.pkl`, and writes a report where **RMSE ≤ 1.0 log units** (see **SC‑002**) and **|Pearson r| ≥ 0.3** (see **SC‑001**) after Bonferroni correction.
2. **Given** the same dataset but targeting `logP`, **When** the command is executed, **Then** analogous artifacts (`ridge_logP.pkl` and report) are produced with performance thresholds **RMSE ≤ 1.0 log units** (see **SC‑007**) and **|Pearson r| ≥ 0.3** (see **SC‑006**) after Bonferroni correction.

---

### User Story 3 – Visualize Entropy vs. Physicochemical Properties (Priority: P3)

A data scientist wants quick visual confirmation of the relationship between entropy scores and the target properties.

**Why this priority**: Visualizations aid interpretation, support manuscript preparation, and help spot outliers or non‑linear patterns that the simple linear model may miss.

**Independent Test**: After training, invoke the `plot_correlation` utility; verify that two PNG files (`entropy_vs_logS.png`, `entropy_vs_logP.png`) are created, each containing a scatter plot with a fitted regression line and axis labels.

**Acceptance Scenarios**:

1. **Given** the model report and the enriched CSV, **When** the user runs `plot_correlation --property logS`, **Then** the system saves `entropy_vs_logS.png` showing atom/bond entropy on the x‑axis and logS on the y‑axis, with a line of best fit and R² displayed, **satisfying SC‑004**.
2. **Given** the same inputs for `logP`, **When** the command is executed, **Then** `entropy_vs_logP.png` is generated with analogous content, **satisfying SC‑004**.

---

### Edge Cases

- What happens when the input CSV contains **zero** molecules?  
  *System SHALL emit a clear error message and abort without creating output files.*

- How does the system handle **non‑ASCII characters** or **invalid atom symbols** in SMILES strings?  
  *System MUST log the offending rows, skip them, and continue processing the remainder.*

- What if the required physicochemical label (e.g., `logS`) is **missing** for a subset of molecules?  
  *System MUST exclude those rows from model training but still include them in the entropy‑only output, noting the omission in a summary log.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (See US-1)**: System MUST ingest a CSV file containing a `smiles` column with up to **10 000** rows.
- **FR-002 (See US-1)**: System MUST compute the **Shannon entropy** of the atom‑type **degree distribution** (topological) for each molecule and store it as `atom_entropy`. (Implemented via RDKit atom degree counting.)
- **FR-003 (See US-1)**: System MUST compute the **Shannon entropy** of the bond‑type **degree distribution** (topological) for each molecule and store it as `bond_entropy`. (Implemented via RDKit bond degree counting.)
- **FR-004 (See US-2)**: System MUST join each molecule with its experimentally measured physicochemical labels (`logS`, `logP`) from the provided metadata columns.
- **FR-005 (See US-2)**: System MUST split the enriched dataset into an **80/20** training/testing partition using a **random split** with a reproducible seed **42**.
- **FR-006 (See US-2)**: System MUST train a **Ridge Regression** model (α = 1.0 by default) for each target property and output:
  - a serialized model file (`*.pkl`),
  - a JSON report containing **RMSE** and **Pearson correlation coefficient** on the test set.
- **FR-007 (See US-3)**: System MUST generate PNG scatter‑plot visualizations of each entropy metric versus each target property, overlaying a linear regression line and reporting **R²**.
- **FR-008 (See US-1)**: System MUST log warnings for malformed SMILES and missing property values, and abort with an informative error if the input file is empty.  
- **FR-009 (See US-1)**: System MUST expose a command‑line interface with sub‑commands `compute_entropy`, `train_model`, and `plot_correlation`.  
- **FR-010 (See US-2)**: System MUST apply a **Bonferroni correction** to p-values for the set of **4 hypothesis tests** (2 entropy types × 2 properties) to control family-wise error rate at **α = 0.05**.
- **FR-011 (See US-2)**: System MUST perform a **sensitivity analysis** on the Ridge Regression regularization parameter (α), sweeping values over the set {0.1, 1.0, 10.0} and reporting the variance in RMSE and Pearson r for the test set.

### Key Entities *(include if feature involves data)*

- **MoleculeRecord**: Represents a single molecule with attributes `smiles`, `atom_entropy`, `bond_entropy`, `logS`, `logP`.
- **RegressionModel**: Serialized Ridge Regression estimator tied to a specific target property.
- **CorrelationPlot**: PNG artifact visualizing the relationship between a chosen entropy metric and a target property.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001 (See US-2)**: Pearson correlation coefficient (|r|) between **atom_entropy** and **logS** on the test set must be **≥ 0.30** AND the adjusted p-value (Bonferroni corrected for 4 tests) must be **< 0.05**.
- **SC-002 (See US-2)**: Root‑Mean‑Square Error for the Ridge Regression model predicting `logS` must be **≤ 1.0** log units on the test set.
- **SC-003 (See US-1)**: The pipeline must successfully process a **10 000‑molecule** dataset in **≤ 30 minutes** on a single‑CPU machine (reference: CPU‑only RDKit performance benchmarks).
- **SC-004 (See US-3)**: Generated correlation plots must be saved as PNG files with a resolution of **≥ 300 dpi** and include axis labels, regression line, and R² annotation (reference: standard scientific figure quality).
- **SC-005 (See US-1)**: The CSV output produced by `compute_entropy` must contain **both** `atom_entropy` and `bond_entropy` columns for every valid input molecule.
- **SC-006 (See US-2)**: Pearson correlation coefficient (|r|) between **atom_entropy** and **logP** on the test set must be **≥ 0.30** AND the adjusted p-value (Bonferroni corrected for 4 tests) must be **< 0.05**.
- **SC-007 (See US-2)**: Root‑Mean‑Square Error for the Ridge Regression model predicting `logP` must be **≤ 1.0** log units on the test set.
- **SC-008 (See US-2)**: Pearson correlation coefficient (|r|) between **bond_entropy** and **logS** on the test set must be **≥ 0.30** AND the adjusted p-value (Bonferroni corrected for 4 tests) must be **< 0.05**.
- **SC-009 (See US-2)**: Pearson correlation coefficient (|r|) between **bond_entropy** and **logP** on the test set must be **≥ 0.30** AND the adjusted p-value (Bonferroni corrected for 4 tests) must be **< 0.05**.
- **SC-010 (See US-2)**: The sensitivity analysis of the regularization parameter (α) must demonstrate that the model performance (RMSE and Pearson r) varies by **< 10%** (relative range: (max - min) / mean) across the tested sweep range {0.1, 1.0, 10.0}, confirming model stability.

## Assumptions

- The execution environment has **Python 3.10+**, **RDKit** installed via `pip install rdkit`, and standard scientific libraries (`numpy`, `pandas`, `scikit‑learn`, `matplotlib`).
- Public FTP endpoints for ZINC15 or ChEMBL provide **SMILES** and associated `logS` / `logP` metadata in CSV format.
- All calculations are performed **CPU‑only**; no GPU resources are required, and no quantization (e.g., 8-bit) is used.
- The random subset of molecules is **representative** of chemical space such that results generalize to larger libraries.
- Users have **read/write** access to the working directory where input CSVs and output artifacts are stored.
- The dataset variables (atom types, bond types, logS, logP) are sufficiently complete in the source data; if specific missing values are encountered, they are handled via exclusion as per FR-008.
- *Note on Baseline*: While the success criteria use an absolute RMSE threshold (≤ 1.0 log units) for clarity, a simple linear model using molecular weight is expected to serve as a reference baseline for context in the final report, though it is not a formal success criterion.
