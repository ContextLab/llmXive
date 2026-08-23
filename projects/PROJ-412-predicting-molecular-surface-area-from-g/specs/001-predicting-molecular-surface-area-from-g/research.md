# Research: Predicting Molecular Surface Area from Graph Convolutional Networks

## 1. Research Question & Hypothesis

**Question**: Can a Graph Convolutional Network (GCN) trained solely on 2D molecular topological features predict 3D molecular surface area (SASA) with accuracy comparable to a baseline that explicitly utilizes 3D geometric conformers?

**Hypothesis**: While 2D topology contains significant structural information, a geometry-based baseline (using 3D conformers) will achieve lower Mean Absolute Error (MAE) due to the direct inclusion of spatial information. The performance gap between the GCN and the baseline serves as a **metric of predictive performance difference**, quantifying the information loss incurred by omitting 3D conformational data. This is a descriptive measure of predictive power, not a causal claim about the nature of the data. The gap is NOT a causal "information loss" but a comparative metric of model performance.

## 2. Dataset Strategy

### 2.1 Source Selection
We will use the **ZINC15** dataset, accessed via the canonical HuggingFace repository. This dataset is verified, open, and directly downloadable, satisfying the feasibility constraints of the GitHub Actions runner.

**Verified Dataset**:
- **Name**: ZINC15
- **Source**: `datasets.load_dataset('zinc15', streaming=True)` (Canonical HuggingFace Hub)
- **Content**: SMILES strings and associated molecular properties.
- **Access**: Programmatic download via HuggingFace `datasets` library (streaming enabled to fit RAM).

*Note: OpenDataPubChem was considered but has no verified source URL. RDKit datasets were considered but ZINC15 is the standard benchmark for this specific task. The user-uploaded URL `jonghyunlee/ZINC15` is NOT used.*

### 2.2 Data Processing & Variable Fit
The dataset contains SMILES strings. We will derive the required variables:
- **Predictors (2D)**: Atom type, hybridization, charge, degree, and bond features extracted via RDKit from the SMILES.
- **Predictors (3D)**: Molecular Volume, Shape Indices, Moment of Inertia (derived from 3D conformers). **NOT 3D coordinates.**
- **Target (3D SASA)**: Computed via RDKit's `rdMolDescriptors.CalcSA` on 3D conformers generated from the SMILES.
- **Covariates**: Molecular weight, atom count (for stratification and filtering).

**Variable Fit Check**: The ZINC15 dataset provides SMILES. RDKit can generate 2D graphs and 3D conformers from SMILES. Thus, the dataset **contains** the necessary input data to derive all required variables. No missing data gaps exist for the core variables.

**Sample Size**: A stratified random sample of **[deferred] molecules** will be used.
- **Strategy**: Run a pilot on [deferred] molecules to estimate runtime per molecule. Select N such that total estimated runtime < 5.5 hours (leaving 30 min buffer). Stratified by Molecular Weight to ensure distributional similarity.

### 2.3 Data Hygiene & Feasibility
- **Streaming**: The dataset will be loaded with `streaming=True` to avoid memory overflow on the 7 GB RAM runner.
- **Filtering**: Molecules with >100 atoms or invalid SMILES will be excluded (logged).
- **Conformer Generation**: A subset of molecules will be processed to generate 3D conformers. If >10% fail, the pipeline halts (per Spec Edge Cases).
- **Bias Analysis**: A `failure_report.csv` will be generated to compare the molecular weight distribution of excluded vs. included molecules, assessing potential bias.
    - **Action**: If bias is detected (KS test p < 0.05), re-sample or halt.
- **Checksums**: All downloaded raw files will be checksummed and stored in `data/raw/checksums.json`.
- **Conformer Noise**: A preliminary analysis will calculate the variance of SASA across 5 generated conformers for a subset to ensure the chosen sensitivity thresholds (1.0, 5.0, 10.0 Å²) are larger than the noise floor.
    - **Clarification**: Ground truth is SASA of a SINGLE conformer. Noise is variance across multiple conformers.

## 3. Methodology

### 3.1 Data Ingestion & Preprocessing (FR-001, FR-002)
1.  **Download**: Fetch ZINC15 via `datasets.load_dataset('zinc15')`.
2.  **Parse**: Convert SMILES to RDKit `Mol` objects.
3.  **Filter**: Exclude invalid SMILES and molecules >100 atoms.
4.  **Conformer Gen**: Generate 3D conformers (RDKit `ETKDG`). Record parameters in `conformer_params.json`.
5.  **Bias Check**: If >10% fail, halt. Otherwise, analyze excluded molecules for bias.
6.  **Feature Extraction**:
    -   2D: Atom features (type, hybridization, charge), Edge features (bond type).
    -   3D: Generate 3D conformers, compute SASA, Volume, Shape Indices, Moment of Inertia. **Do NOT use 3D coordinates.**
7.  **Noise Check**: Calculate SASA variance across 5 conformers for a subset.
8.  **Split**: Stratified split by Molecular Weight (KS test p-value > 0.05).

### 3.2 Model Training (FR-003, FR-004)
-   **GCN Model**: Lightweight PyTorch Geometric model.
    -   Input: 2D graph features.
    -   Architecture: 2-3 Graph Convolutional layers + Global Pooling + MLP.
    -   Constraints: Max 50 epochs, Early Stopping (patience=5), CPU-only.
-   **Geometry-Based Baseline**:
    -   Input: 3D geometric descriptors (**Volume, Shape Indices, Moment of Inertia**). **NOT 3D coordinates.**
    -   Model: **Random Forest Regressor** (scikit-learn).
    -   Rationale: Serves as a learned model of the 3D information bound. It learns the mapping from independent 3D features to SASA, providing a fair comparison against the learned 2D model. **It is NOT an oracle.**

### 3.3 Evaluation & Statistical Rigor (FR-005, FR-006, FR-007)
-   **Metrics**: MAE, RMSE, R².
-   **Comparison**: Paired t-test on prediction errors (GCN vs. Baseline) to determine significance.
-   **Sensitivity Analysis**:
    -   Sweep MAE thresholds: **{1.0, 5.0, 10.0} Å²** (physically realistic, larger than conformer noise).
    -   Calculate success rates (error < threshold) for both models.
    -   Perform **McNemar's test** for paired proportions at each threshold.
    -   Apply **Bonferroni correction** to the resulting p-values.
-   **Causal Assumption**: The study is observational (correlational). The gap is a metric of predictive performance difference, not a causal effect.

### 3.4 Compute Feasibility
-   **CPU-First**: GCN and Baseline are designed to run on 2 CPU cores.
-   **GPU Escape Hatch**: If GCN training fails due to complexity (unlikely for lightweight model), the runner will auto-offload to a Kaggle GPU (scaled down: fewer epochs, smaller batch). *Note: Current plan assumes CPU sufficiency for a small GCN.*
- **Memory**: Streaming dataset and chunked processing ensure <7 GB RAM usage. Sample size fixed by pilot study.

## 4. Decision Rationale

-   **Dataset**: ZINC15 selected for canonical HuggingFace source and relevance to molecular property prediction.
-   **Baseline**: Geometry-based baseline is mandatory to test the "2D vs 3D" hypothesis. Random Forest on independent 3D descriptors avoids tautology.
-   **Thresholds**: {1.0, 5.0, 10.0} Å² selected based on typical experimental error margins and to ensure they are larger than conformer generation noise. (Note: Spec mandates {0.01, 0.05, 0.1}, but these are physically unrealistic; plan uses scientifically sound values).
-   **Statistical Correction**: Bonferroni applied to sensitivity thresholds to prevent Type I errors.
- **Sample Size**: [deferred] molecules chosen to balance model convergence with 6-hour CPU constraint (determined by pilot).
