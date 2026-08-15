# Research: Predicting Molecular Surface Area from Graph Convolutional Networks

## Executive Summary

This research validates the hypothesis that 2D topological features (atom types, bonds) are sufficient to predict 3D molecular surface area (SASA) with accuracy comparable to methods explicitly using 2D descriptors. We compare a Graph Convolutional Network (GCN) against a **2D Topology Baseline** (Gradient Boosting Regressor on 2D descriptors). A **Geometry Oracle** (direct RDKit calculation) is used as a deterministic upper bound reference. The study uses the `zhangh1990/zinc` dataset from HuggingFace, processed via RDKit with MMFF94 minimization. Statistical significance is assessed via paired t-tests on absolute errors (continuous) and McNemar's test for binary outcomes, with multiple-comparison correction.

## Dataset Strategy

### Verified Sources
We utilize the **ZINC15** subset available on HuggingFace, specifically the `zhangh1990/zinc` dataset, which is verified as a direct, programmatic download source.

| Dataset Name | Source URL | Load Method | Rationale |
|--------------|------------|-------------|-----------|
| ZINC15 | `https://huggingface.co/datasets/zhangh1990/zinc` | `datasets.load_dataset("zhangh1990/zinc", split="train")` | Contains a substantial collection of unique SMILES strings. Verified as open, directly downloadable, and suitable for graph generation. **Note**: This dataset provides SMILES strings only; 3D conformers are generated locally via RDKit, not pre-computed in the dataset. |

**Data Availability Note**: 
- **OpenDataPubChem**: No verified source found in the provided list. We **do not** use this source.
- **Access-Gated Data**: No access-gated data (e.g., ADNI, UK Biobank) is required. The ZINC15 subset is fully open.
- **Streaming**: The full ZINC dataset may exceed several gigabytes. We will use `streaming=True` in the HuggingFace `datasets` loader to process molecules in batches, accumulating statistics online to stay within RAM limits. If the full dataset cannot be processed within a reasonable timeframe, we will sample a subset of rows (fixed seed) and note the power limitation. The current dataset size is within the available RAM constraint and will be processed in full (capped at 50k).

### Data Processing Pipeline

1.  **Ingestion**: Download `zhangh1990/zinc`. Validate SMILES syntax using RDKit. Exclude invalid entries. **Schema Validation**: Confirm the dataset contains a `smiles` column and no pre-computed 3D data.
2.  **2D Feature Extraction**: Convert valid SMILES to RDKit `Mol` objects. Extract node features (atomic number, hybridization, formal charge, degree) and edge features (bond type, conjugation).
3.  **3D Label Generation**:
    - Generate 3D conformers for a subset of molecules using RDKit's `ETKDG` algorithm.
    - **Minimization**: Perform **MMFF94 energy minimization** on the generated conformers to ensure the 'ground truth' SASA is derived from a stable local minimum, reducing label noise from heuristic artifacts.
    - **Constraint**: If 3D generation fails for >10% of the batch, halt and log.
    - Calculate SASA (Solvent Accessible Surface Area) using the `rdkit.Chem.rdMolDescriptors.CalcASA` function on the minimized conformer.
    - **Logging**: Log conformer generation parameters (attempts, seed, minimization steps, tolerance) to `data/processed/conformer_params.json`.
4.  **Dataset Construction**: Merge 2D graph features and 3D SASA labels into `data/processed/paired_dataset.parquet`.
5.  **Splitting**: 
    - **Scaffold Split**: Perform a scaffold split (Bemis-Murcko) to ensure the test set contains structurally novel molecules not present in the training set, controlling for conformational diversity and stereochemistry shifts.
    - **Stratified Split**: Additionally, stratify by molecular weight (MW) to ensure training/test distributions are similar (KS test p-value > 0.05).

## Model Strategy

### 1. Graph Convolutional Network (GCN)
- **Architecture**: 3-layer GCN with ReLU activation and batch normalization.
- **Input**: Node feature matrix (atoms) and edge index (bonds).
- **Output**: Single scalar (predicted SASA).
- **Training**: 
  - Loss: Mean Squared Error (MSE).
  - Optimizer: Adam (lr=1e-3).
  - Early Stopping: Patience=5 epochs, min_delta=1e-4.
  - Max Epochs: 50 (as per FR-003).
  - Hardware: CPU-only (PyTorch default).
- **Rationale**: GCNs are state-of-the-art for 2D graph property prediction. This architecture is lightweight enough for the 7GB RAM constraint.

### 2. 2D Topology Baseline (Trained Model)
- **Approach**: Gradient Boosting Regressor (GBR).
- **Features**: 2D molecular descriptors calculated via RDKit (from the 2D graph):
  - Molecular Weight
  - Number of Atoms
  - Number of Bonds
  - LogP (octanol-water partition coefficient)
  - Number of Rotatable Bonds
  - **Exclusion**: No 3D geometric descriptors (e.g., Volume, Radius of Gyration) are used.
- **Training**: Fit on the same training split as the GCN.
- **Rationale**: This baseline represents a robust, non-linear 2D-only predictive model. Comparing GCN (2D) to this (2D) tests the sufficiency of 2D topology in a fair, non-tautological manner. The use of GBR (non-linear) ensures a fair comparison against the GCN.

### 3. Geometry Oracle (Deterministic)
- **Approach**: Direct calculation of SASA from the minimized 3D conformer.
- **Purpose**: Used as a theoretical upper bound (error ≈ 0) and for sensitivity analysis, but **NOT** used for the primary paired t-test comparison (FR-005). The primary comparison is between the GCN and the **2D Topology Baseline**.

## Statistical Rigor & Methodology

### Hypothesis Testing
- **Primary Hypothesis**: $H_0$: MAE(GCN) = MAE(2D Baseline); $H_1$: MAE(GCN) < MAE(2D Baseline).
- **Test**: Paired t-test on the **absolute errors** (point-wise) of the GCN and the 2D Topology Baseline.
- **Fallback**: If the error distribution is non-normal (e.g., many zeros), use the Wilcoxon signed-rank test.
- **Correction**: Bonferroni correction applied if multiple thresholds are tested (FR-007).
- **Effect Size**: Cohen's d reported alongside p-values.

### Multiple Comparison Correction
- **Scenario**: Sensitivity analysis sweeps thresholds across a range of Å² values.
- **Action**: If we perform a hypothesis test for each threshold (e.g., "Is success rate > X%?"), we apply Bonferroni correction.
- **Logic**: If N thresholds > 1, apply Bonferroni correction to the p-values derived from **McNemar's tests** for binary success rates.
- **Rationale**: Prevents Type I error inflation (FR-007).

### Power & Sample Size
- **Limitation**: We acknowledge the power limitation if the dataset is sampled (e.g., 50k molecules). We will report the effective sample size and note that smaller effect sizes may not be detectable. The current dataset is considered sufficient for this task.
- **Causal Claims**: None. The study is observational (predictive modeling). Claims are framed as associational (2D topology predicts SASA).

### Measurement Validity
- **Instruments**: RDKit's `CalcASA` is the standard for computed SASA. We cite RDKit documentation as the validation source.
- **Collinearity**: In the baseline, descriptors like "Number of Atoms" and "Volume" may be collinear. We will report Variance Inflation Factors (VIF) and acknowledge if independent effects cannot be disentangled.
- **Conformational Uncertainty**: The "ground truth" is explicitly defined as the SASA of the minimized ETKDG conformer. For flexible molecules, this is an approximation of the ensemble average. The model learns to predict this specific conformer's SASA. This limitation is documented in the final report.
- **Proxy Limitation**: The study validates the predictive capability of 2D topology relative to the RDKit SASA proxy, not the absolute physical truth.

### Sensitivity Analysis (FR-006, SC-004)
- **Thresholds**: Sweep MAE cutoffs: {0.01, 0.05, 0.1} Å².
- **Metric**: Report the variation in success rates (percentage of molecules predicted within the threshold).
- **Variation Metric**: Calculate the **range (max - min)** and **slope** of the success rate curve across thresholds.
- **Justification**: The primary threshold is justified by typical experimental error margins in surface area measurement (Assumption in spec.md).
- **Output Schema**: The sensitivity report must explicitly include columns: `threshold`, `success_rate`, `adjusted_p_value`.

### Computational Feasibility (SC-005)
- **Measurement**: Record total runtime on the CPU-only runner.
- **Requirement**: Compare total runtime against the 6-hour CI limit in the final report. This measurement is an explicit step in the evaluation phase.

## Decision/Rationale: Compute Strategy

- **CPU-First**: The GCN architecture (3 layers, ~10k parameters) and dataset size (≤50k) are computationally tractable on a 2-core, 7GB RAM CPU. No GPU is required for training or inference.
- **GPU Escape Hatch**: Not anticipated. If the GCN training exceeds 6 hours or crashes due to OOM, the execution stage will auto-offload to Kaggle GPU. However, the plan is designed to run entirely on CPU to avoid unnecessary complexity.
- **Streaming**: To handle large datasets, we stream from HuggingFace, processing in chunks of molecules. This ensures we never load the full dataset into RAM.

## Constitution Alignment

- **Reproducibility**: All seeds (random, numpy, torch, RDKit) are pinned.
- **Data Hygiene**: Checksums of raw data recorded. No in-place modifications.
- **Geometric Fidelity**: Explicit comparison between 2D (GCN) and 2D Topology (GBR Baseline) methods. The Geometry Oracle is a reference only.
- **Conformational Sampling**: Conformer params logged; failure rates tracked.
