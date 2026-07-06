# Research: Predicting Alloy Phase Diagrams from Compositional Data

## 1. Problem Statement & Hypothesis

**Problem**: Predicting phase boundaries (liquidus/solidus) typically requires complex thermodynamic simulations (CALPHAD). This project investigates if simple compositional descriptors alone can approximate these boundaries for simple binary systems.

**Hypothesis**: Compositional descriptors (mean atomic radius, electronegativity variance, valence electron concentration, Hume-Rothery electron concentration) contain sufficient information to predict phase transition temperatures for simple binary systems with a **Topological Consistency Score (TCS) ≥ 0.8** and **Pointwise MAE ≤ 50K**.

## 2. Dataset Strategy

### 2.1 Primary Data Sources & Verification

The Spec mandates data from **NIST-JANAF** and **SGTE**.

- **Verification Protocol**:
  1. Check the "Verified datasets" input block for URLs corresponding to NIST-JANAF or SGTE.
  2. **If Found**: Use the verified URL.
  3. **If Not Found**: **HALT** with error code `DATA_SOURCE_MISSING`.
     - *Rationale*: Using unverified proxies (e.g., synthetic HuggingFace datasets) violates the Spec's requirement for experimental ground truth and the Constitution's Principle II (Verified Accuracy).

- **Note on Proprietary Data**: NIST-JANAF and SGTE are proprietary. If the verified input block does not contain accessible links to these specific databases, the project cannot proceed with the Spec's exact data requirement. The pipeline will not substitute with unverified or synthetic data.

### 2.2 Dataset Verification & Fit

**Critical Check**: Does the dataset contain the required variables?
- **Required Variables**:
  - `element_a`, `element_b` (Binary system definition)
  - `composition_a` (Mole fraction of element A)
  - `temperature` (Phase boundary temperature)
  - `phase_type` (e.g., liquidus, solidus)
- **Verification**: Perform an initial schema check in `code/ingest/load_data.py`.
  - *If missing*: Halt with `INVALID_DATA_SCHEMA` (FR-001).
  - *If ternary only*: Filter for binary systems. If none exist, `LOW_DATA_DENSITY` (FR-008).

### 2.3 Data Loading Strategy

1.  **Load**: Use `pandas.read_parquet` or `read_csv` from the verified URL.
2.  **Filter**:
    - Keep only rows where `temperature` is not null.
    - Keep only binary systems.
    - Exclude complex/metastable systems (e.g., Fe-C) if identifiable.
3.  **Fallback**: No fallback to unverified URLs. If the verified source fails (network error), retry 3 times with exponential backoff (FR-07). If all fail, halt with `API_RATE_LIMIT_EXCEEDED`.

## 3. Methodology

### 3.1 Descriptor Generation (FR-002, FR-015)

For each alloy composition, calculate:
1.  **Mean Atomic Radius**: $\sum x_i \cdot r_i$
2.  **Electronegativity Variance**: $\sum x_i \cdot (EN_i - \overline{EN})^2$
3.  **Valence Electron Count (VEC)**: $\sum x_i \cdot VEC_i$
4.  **Hume-Rothery Electron Concentration**: Derived from VEC and atomic radius differences.

*Constants Source*: Elemental properties loaded from `data/raw/elemental_properties.csv`.

### 3.2 Model Training & Validation (FR-003, FR-010)

- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Validation Strategy**: **Leave-One-System-Out (LOSO)**.
  - **Logic Correction**: In a binary alloy dataset, holding out a system (e.g., Cu-Zn) *always* removes Cu and Zn from the training set. Thus, the test set *always* contains "new elements" relative to the training set.
  - **FR-010 Compliance (Property Range Extrapolation)**:
    - The "New Element" constraint is reinterpreted as a check for **Extrapolation**.
    - **Method**: Compute the convex hull of elemental properties (radius, EN) in the *training set*.
    - **Decision**:
      - If the test set's elements fall **inside** the training convex hull: Proceed (Interpolation).
      - If the test set's elements fall **outside** the training convex hull: **Skip Fold** (Extrapolation).
    - This ensures the model is not tested on properties it has never seen, while still testing "new systems".

### 3.3 Power Analysis (FR-011)

- **Unit of Analysis**: Number of **Systems** (K), not total data points.
- **Effect Size Definition**:
  - **Minimum Detectable Effect (MDE)**: R² improvement of **0.10** over the Null Model.
  - **Cohen's f²**: ≈ 0.11 (Small-to-Medium).
- **Variance Estimation**:
  - Perform a pilot run with a Null Model (predicting mean of training fold) to estimate the variance of errors ($\sigma^2$).
  - Use this $\sigma^2$ to calculate the non-centrality parameter for the power analysis.
- **Target**: Power ≥ 0.8 at α ≤ 0.05.
- **Action**: If Power < 0.8, halt with `INSUFFICIENT_POWER`.

### 3.4 Evaluation Metrics (FR-004, SC-001, SC-002, SC-004, SC-009)

1.  **Pointwise Accuracy**:
    - **MAE**: Mean Absolute Error. Target ≤ 50K.
    - **R²**: Coefficient of determination.
2.  **Visual Fidelity (Topological Consistency Score - TCS)**:
    - **Definition**: Measures if the *order* of phase boundaries is correct.
    - **Algorithm**:
      - For a given system, sample temperatures at fixed composition slices (e.g., 0.1, 0.2, ... 0.9).
      - Sort predicted temperatures and experimental temperatures.
      - TCS = 1.0 if `sorted(predicted) == sorted(experimental)`, else partial match ratio.
    - **Target**: TCS ≥ 0.8.
3.  **Baseline Comparison (FR-009, SC-008)**:
    - **Null Model**: Trained on the *training fold* (predicting mean of training fold).
    - **Significance**: **Permutation Test** (10,000 iterations) on the distribution of fold-level MAE differences.
      - *Hypothesis*: RF MAE is not better than Null Model MAE by chance.
      - *Result*: p-value. Target p < 0.05.
4.  **Data Density Check (FR-013, SC-009)**:
    - **Process**:
      - Aggregate prediction errors by `system_id`.
      - Calculate **Standard Deviation (SD)** of errors per system.
    - **Trigger**: If SD > 50K OR N < 5, flag `LOW_DATA_DENSITY`.
    - **Reporting**: Include per-system SD in `model_metrics.json`.

### 3.5 Computational Feasibility

- **Hardware**: Single CPU core, <7 GB RAM.
- **Optimization**:
  - Limit `n_estimators` to 100.
  - Process data in chunks if > 1 GB.
  - No GPU/CUDA.
  - Time limit: a defined duration.

## 4. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Data Source Missing** | Halt with `DATA_SOURCE_MISSING` if NIST/SGTE not in verified block. |
| **Property Extrapolation** | Skip folds where test elements are outside training convex hull. |
| **Low Data Density** | Trigger `LOW_DATA_DENSITY` error if SD > 50K. |
| **Power < 0.8** | Halt with `INSUFFICIENT_POWER` if K < required for MDE=0.10. |
| **API Failure** | Exponential backoff (3 retries) + Halt if verified source unreachable. |
| **Memory Overflow** | Stream processing or subsampling; monitor memory usage. |