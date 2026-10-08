# Research: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Scientific Background

The diffusion of atoms in solids is a thermally activated process described by the Arrhenius equation:
$D = D_0 \exp(-Q/RT)$
where $Q$ is the activation energy. In FCC metals, alloying elements can significantly alter $Q$ due to lattice strain (size mismatch) and electronic interactions. This project focuses on quantifying the impact of the **size mismatch** descriptor ($\Delta r / r_{host}$) on the shift in activation energy ($\Delta Q$).

**Methodological Correction**: The hypothesis requires variation in solute properties. Therefore, the analysis uses **solute diffusion** data (solute != host) for training, while **self-diffusion** data (solute = host) is used exclusively to determine the baseline activation energy ($Q_{host}$) for each host metal.

## Dataset Strategy

### Primary Data Source
The project relies on the **NIST Standard Reference Database 150 (Diffusion in Solids)**.
*   **Requirement**: The dataset must contain `crystal_structure`, `diffusion_mode`, `host_element`, `solute_element`, `concentration`, and `activation_energy`.
*   **Constraint**: 
    *   **Training Set**: `crystal_structure == "FCC"` AND `diffusion_mode == "solute"` (or "impurity").
    *   **Baseline Set**: `crystal_structure == "FCC"` AND `diffusion_mode == "self"`.
*   **Availability Check**: The pipeline MUST halt if no verified real dataset is found. **Synthetic data is strictly forbidden** as a substitute for the primary research goal.

### Verified Sources & Access
*   **NIST SRD 150**: The spec assumes a verified programmatic source exists.
    *   *Critical Risk*: The provided "Verified datasets" list does **not** contain a verified URL for NIST SRD 150. 
    *   *Implementation*: The `code/data/streaming_loader.py` script will attempt to fetch data from a verified public mirror (e.g., HuggingFace if available) or a direct URL if provided in the environment. 
    *   *Halt Condition*: If no verified source is found, the script halts with: "ERROR: No verified real dataset found. Synthetic data is not permitted for this research goal."
    *   *No Fallback*: The plan does **not** permit a "pre-curated CSV" unless it is cryptographically signed and verified against the NIST source.

### Data Processing Plan
1.  **Ingestion**: `code/data/streaming_loader.py` loads raw data (CSV/JSONL).
2.  **Split**: 
    *   **Baseline Set**: Filter `diffusion_mode == "self"`. Extract $Q_{host}$ for each unique `host_element`.
    *   **Training Set**: Filter `diffusion_mode == "solute"`.
3.  **Baseline Validation**: For every host in the Training Set, verify a corresponding entry exists in the Baseline Set. If missing, halt with: "ERROR: Baseline activation energy for host [X] not found in NIST SRD 150. Pipeline halted." (FR-006).
4.  **Cleaning**: Remove rows with missing `solute_concentration` or `activation_energy`. Log excluded rows to `errors/missing_data.csv`.
5.  **Merging**: Merge Training Set with Baseline Set on `host_element` to calculate `baseline_shift_eV` ($Q_{alloy} - Q_{pure\_host}$).
6.  **Streaming**: If the dataset > 7GB, use `pandas.read_csv(..., chunksize=...)` to process in batches, accumulating statistics without loading the full file into RAM.

## Feature Engineering

### Atomic Descriptors
1.  **Size Mismatch ($\Delta r / r_{host}$)**:
    *   Formula: $(r_{solute} - r_{host}) / r_{host}$
    *   Source: `periodictable==0.20.1` library (version pinned in `requirements.txt` for consistency).
2.  **Electronegativity Difference ($\Delta \chi$)**:
    *   Formula: $|\chi_{solute} - \chi_{host}|$
    *   Source: Pauling scale (consistent with Constitution Principle VII).
3.  **Valence Electron Count (VEC)**:
    *   Source: `periodictable` library.

### Derived Features
*   **Baseline Shift ($\Delta Q$)**: $Q_{alloy} - Q_{pure\_host}$.
*   **Concentration Normalization**: Ensure concentration is in atomic percent (at.%).

## Model Strategy

### 1. Random Forest (RF) & Gradient Boosting (GB)
*   **Purpose**: High-accuracy prediction of $\Delta Q$.
*   **Library**: `scikit-learn` (CPU-only).
*   **Hyperparameter Tuning**:
    *   Grid Search: `max_depth` [3, 10], `n_estimators` [50, 200].
    *   Metric: Maximize $R^2$.
    *   Tie-breaking: Lowest complexity (lowest depth, then lowest estimators).
*   **Validation**: Nested Cross-Validation (default) or 80/20 Hold-out (if N < 50).
*   **Compute**: Fully CPU-tractable. No GPU needed.

### 2. Linear Regression (LR)
*   **Purpose**: Statistical inference (significance of `size_mismatch`).
*   **Output**: Coefficient, standard error, p-value, 95% bootstrap CI.
*   **Hypothesis**: $H_0: \beta_{size\_mismatch} = 0$.
*   **Compute**: CPU-tractable.

## Statistical Rigor & Validation

### Significance Testing
*   **Method**: Bootstrap resampling for the Linear Regression coefficient.
*   **Metric**: P-value < 0.05 indicates statistical significance.
*   **Confidence Interval**: % CI must not include 0.

### Sensitivity Analysis (Threshold Stability)
*   **Threshold Sweep**: 0.45, 0.46, ..., 0.55 eV.
*   **Metric**: Stability Index = $\frac{\sigma(\text{classification rates})}{\text{max\_threshold} - \text{min\_threshold}}$.
*   **Target**: Stability Index ≤ 0.05 $eV^{-1}$.
*   **Definition**: "Significant shift" = $\Delta Q > \text{threshold}$.

### Multiple Comparison Correction
*   Since multiple models are tested, but the primary hypothesis is specific to the `size_mismatch` coefficient in the Linear model, a Bonferroni correction is applied if multiple independent hypotheses are tested simultaneously. For the single primary descriptor, standard p-values are reported with the bootstrap CI.

## Compute Feasibility (CPU-First)

*   **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, ~7 GB RAM).
*   **Models**: RF, GB, and Linear Regression are standard CPU algorithms in `scikit-learn`.
*   **Data Size**: Expected dataset size < 10 MB.
*   **Runtime**: Grid search on small datasets (<500 rows) completes in < 15 minutes.
*   **GPU Escape Hatch**: Not required for this methodology.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No verified NIST dataset found** | Fatal (Project Halts) | `streaming_loader.py` halts with explicit error. No synthetic data used. |
| **Dataset too small (<50 rows)** | Low Power | Switch to a strict hold-out split; report power limitation in final report. |
| **Single host metal** | Stratification fail | Fall back to random split; log warning. |
| **Missing atomic radii** | Data loss | Exclude row, log to `errors/missing_atomic_data.csv`. |
| **R² < 0.1** | Null result | Save model, flag as "Low Predictive Power" (valid scientific outcome). |
| **Missing Host Baseline** | Fatal | `baseline.py` halts with specific error message (FR-006). |