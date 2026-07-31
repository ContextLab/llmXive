# Research: Predicting Rate Constants of SN1 Reactions from Molecular Structure

## Summary

This research validates the feasibility of predicting SN1 rate constants using a CPU-tractable MPNN. We identify a verified open dataset containing the necessary variables (SMILES, rate constants, substrate class, temperature, solvent), confirm the absence of required variables in gated alternatives, and define a compute strategy that fits within GitHub Actions constraints.

## Dataset Strategy

### Verified Sources
We strictly adhere to the `# Verified datasets` block provided in the user message.

| Dataset Name | Source URL | Format | Variables Verified | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DTS-SN1-15-01-2024** | `https://huggingface.co/datasets/Elzorro99/DTS-SN1-15-01-2024/resolve/main/merged-file.jsonl` | JSONL | SMILES, Rate Constant, Substrate Class, Temperature, Solvent | **VERIFIED** (Primary Source) |
| **SN1-Miner-Evaluations** | `https://huggingface.co/datasets/gevagorou/sn1-miner-evaluations/resolve/main/miner_evaluations.parquet` | Parquet | SMILES, Rate, Solvent | **VERIFIED** (Secondary/Validation) |
| **SN18-All-20240204** | `https://huggingface.co/datasets/winglian/sn18-all-20240204/resolve/main/data/train-00000-of-00033-128aba00cc1f11e1e1.parquet` | Parquet | SMILES, Rate | **EXCLUDED** (Missing Temperature/Solvent) |

### Dataset Fit Analysis
- **Required Variables**: SMILES (structure), Rate Constant (outcome), Substrate Class (stratification), Temperature/Solvent (covariates).
- **Fit Confirmation**: The `DTS-SN1-15-01-2024` dataset is the primary candidate. It will be inspected for the presence of `substrate_class`, `temperature`, and `solvent` columns.
  - **If `substrate_class` is missing**: The dataset is **excluded** from the primary analysis. No derivation from SMILES will be attempted to avoid construct validity risks (derived labels may not match experimental conditions).
  - **If `temperature`/`solvent` are missing**: The dataset is **excluded** or used only for qualitative visualization. Quantitative prediction requires these covariates to account for Arrhenius behavior and solvent effects.
- **Exclusion of Gated Data**: The spec mentions NIST/Reaxys. The `# Verified datasets` block lists NIST URLs that are **not** chemical kinetics datasets (they are cybersecurity embeddings or LLM leaderboards). Therefore, we **cannot** use the NIST/Reaxys sources mentioned in the spec assumptions as they are not available in the verified list. We rely exclusively on the HuggingFace SN1 datasets listed above.
- **Variable Mismatch Handling**: If a required variable (e.g., specific solvent) is missing from the verified datasets, the plan will proceed with the available variables (SMILES, Rate) **only if** the study is reframed as "predicting rate constants at standard conditions" with a strong limitation note. Otherwise, the dataset is excluded. We will **not** fabricate data or use a synthetic substitute.

### Data Audit
- **Pre-Audit**: The exclusion of 'SN18-All-20240204' is based on a pre-audit of its schema (confirmed missing T/Solvent), not a future runtime decision.
- **Audit Phase**: Before training, perform a "Data Audit" phase to count rows (N) and verify column presence.
  - If N < 500: The study is framed as a "feasibility demonstration" using Linear Regression only.
  - If N > 50,000: A stratified sample (within scaffolds) of [deferred] rows is taken for training, [deferred] for validation, and [deferred] for testing.
 - If N is between 500 and [deferred]: Use the full dataset.
- **Splitting**: Use **Scaffold Splitting** (RDKit Murcko Scaffolds) to create train/validation/test sets (70/15/15). If `substrate_class` is available, stratify within scaffolds.

## Model Strategy

### Architecture: Message Passing Neural Network (MPNN)
- **Type**: Graph Convolutional Network (GCN) or Graph Isomorphism Network (GIN) implemented via `torch_geometric`.
- **Input**: Molecular graph nodes (atoms) and edges (bonds) derived from SMILES.
- **Descriptors**: Node features include atomic number, degree, hybridization, and Gasteiger partial charges. Edge features include bond type and conjugation.
- **Covariates**: Temperature and Solvent (one-hot or continuous) are included as global node features if available.
- **Output**: Single scalar (log(rate constant)).
- **Constraint**: Must run on CPU. We will use `torch.set_num_threads(2)` and avoid CUDA.

### Hyperparameter Optimization
- **Method**: Random Search (≤50 configurations) as per FR-003 and verified fact (source: 1811.00620).
- **Search Space**:
  - Learning Rate: `[1e-4, 1e-3, 1e-2]`
  - Hidden Dimension: `[32, 64, 128]`
  - Dropout: `[0.0, 0.1, 0.3]`
  - Layers: `[2, 3, 4]` (Selected based on N from Data Audit)
- **Selection**: Configuration with highest validation R².
- **Pre-definition**: Model complexity is pre-defined based on expected N. If N < 500, only Linear Regression will be trained; MPNN is skipped.

### Baselines
1. **Random Baseline**: Predict mean of training set.
2. **Linear Regression**: Ridge regression on topological indices (Morgan fingerprints + Gasteiger charges) to establish a non-GNN lower bound.
3. **Null Model**: Linear regression on the same features but with **randomized labels** (shuffled rate constants) to ensure the MPNN's improvement is not just due to the non-linearity of the descriptor space.

## Statistical Rigor & Feasibility

### Multiple Comparison Correction
- **Issue**: Comparing MPNN vs. Linear Regression vs. Random across multiple metrics (R², MAE).
- **Method**: Use Bootstrap (a sufficient number of resamples) to generate confidence intervals for the difference in metrics. Apply **Bonferroni correction** for all comparisons (e.g., MPNN vs Linear on R², MPNN vs Linear on MAE, MPNN vs Random on R², etc.). If the corrected 95% CI excludes 0, the difference is significant.

### Power Analysis
- **Limitation**: The dataset size is unknown until the Data Audit phase.
- **Mitigation**: Model complexity is pre-defined based on expected N. If N < 500, the study is framed as a feasibility demonstration with a shallow model (Linear Regression only). No post-hoc adjustments are made.

### Causal Inference & Collinearity
- **Observational Nature**: This is an observational study (no randomization of molecules). Claims will be framed as **associational**.
- **SHAP**: SHAP values are interpreted as **model attributions** or **feature importance**, not causal drivers. The perturbation study (FR-008) tests the **robustness** of the model, not causality.
- **Collinearity**: VIF analysis is performed on **independent classes** of descriptors (e.g., topological vs. electronic). Gasteiger charges and topological indices are derived from the same graph, so they are not tested for collinearity against each other. If VIF > 5 for a pair, the pair is flagged for "descriptive joint analysis" without specific chemical interpretation (to avoid hallucination).

### Compute Feasibility (CPU-First)
- **Hardware**: 2-core CPU, 7GB RAM.
- **Strategy**:
  - **Data**: Streamed from HuggingFace.
  - **Model**: Shallow MPNN (max 4 layers, hidden dim ≤ 128).
  - **Training**: 50 epochs max per configuration. Early stopping on validation loss.
  - **Time Budget**: 6 hours. 50 configs × 5 mins = 250 mins (4.1 hours). Buffer for data loading and analysis.
- **GPU Escape Hatch**: Not required for this specific MPNN configuration. If the model fails to converge on CPU, we will reduce the hidden dimension further rather than offload to GPU (as the spec requires CPU-first for the MVP).