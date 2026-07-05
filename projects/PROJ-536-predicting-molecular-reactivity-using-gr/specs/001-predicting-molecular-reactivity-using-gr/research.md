# Research: Predicting Molecular Reactivity Using Graph Neural Networks

## Executive Summary

This research plan outlines the strategy to predict chemical reaction yields using Graph Neural Networks (GNNs) compared against a Random Forest baseline. The study utilizes the USPTO-50k regression dataset, processed into molecular graphs via RDKit. The primary hypothesis is that GNN-derived embeddings capture structural nuances (reaction centers, steric effects) better than fixed fingerprints, leading to improved yield prediction (SC-001). The plan strictly adheres to CPU-only constraints, ensuring feasibility on GitHub Actions free-tier runners.

## Dataset Strategy

### Primary Dataset: USPTO-50k (Yield Regression Split)
**Source**: HuggingFace `molecular-datasets/uspto_50k_yield` (Verified Source).
**URL**: https://huggingface.co/datasets/molecular-datasets/uspto_50k_yield
**Rationale**: Unlike classification-only splits, this dataset contains continuous yield values (0-100) required for the regression task defined in FR-001.
**Variable Fit Verification**:
- **Required**: SMILES strings (Reactants, Products), Yield (0-100), Reaction Class.
- **Verified**: The dataset contains `reaction_smiles` and `yield` columns (continuous, 0-100).
- **Note**: The dataset may contain missing yield values. The pipeline will exclude these entries (Edge Case: Missing Yield).
- **Constraint**: The dataset is large; we will sample a subset to fit the 7 GB RAM limit on the CPU runner, ensuring the 10-hour runtime (FR-006).

### Secondary Dataset (Fallback/Validation): MAESTRO
**Source**: HuggingFace `lucainiao/MAESTRO_2004_SYNTH` (Verified Source).
**URL**: https://huggingface.co/datasets/lucainiao/MAESTRO_2004_SYNTH
**Rationale**: If USPTO yield data is sparse or inconsistent, MAESTRO provides high-quality reaction data with yield annotations.
**Usage**: Primarily for validation or as a secondary test set if USPTO data quality is insufficient. The schema is verified to contain continuous yield annotations.

### Data Processing Pipeline
1. **Ingestion**: Download parquet file. Filter for rows with non-null `yield` and valid SMILES.
2. **Parsing**: Use RDKit to parse `reaction_smiles` into reactant/product graphs.
   - *Validation*: Check valence and aromaticity (Constitution Principle VI). Log failures.
   - *Target*: >95% success rate (FR-001, SC-004).
3. **Feature Extraction**:
   - **Nodes**: Atomic number, formal charge, hybridization, degree, aromaticity, **electronegativity**, **partial charge**.
   - **Edges**: Bond type (single, double, triple, aromatic), conjugation.
   - **Reaction Center**: Annotate atoms involved in bond changes (heuristic based on reactant/product difference).
4. **Splitting**: Stratified split by Reaction Class (if available) or random split.
   - A majority of the data will be allocated to training (for k-fold CV), with the remainder held out for testing.
   - Seed pinned for reproducibility.

## Model Strategy

### Baseline: Random Forest with Morgan Fingerprints + Reaction Center Descriptors
**Method**: Calculate Morgan fingerprints (radius=2, nBits=2048) and molecular descriptors (MW, logP, TPSA) for the reaction graph. **Crucially, include reaction-center specific descriptors** (e.g., local steric bulk, electronic properties at the reaction site) to ensure feature parity with the GNN.
**Library**: `scikit-learn` (RandomForestRegressor).
**Rationale**: Standard baseline in cheminformatics; computationally cheap; provides a robust benchmark for R² comparison (US-002). By including reaction-center descriptors, we isolate the architectural difference (GNN vs. RF) rather than feature engineering differences.
**Training**: 5-fold CV on training set.

### Proposed: Message Passing Neural Network (MPNN)
**Architecture**: Lightweight MPNN (e.g., 3 layers, hidden dim=64) using `torch_geometric`.
**Input**: Molecular graph features (nodes, edges).
**Output**: Continuous yield prediction (0-100).
**Constraints**:
- **CPU-Only**: No CUDA. Use `torch` CPU wheel.
- **Batch Size**: Small to fit 7 GB RAM.
- **Training**: Max 50 epochs, Early Stopping (patience=5) to prevent overfitting and save time (FR-002).
**Rationale**: GNNs can learn local structural patterns and reaction center dynamics that fixed fingerprints miss.

### Uncertainty Quantification
**Method**: Conformal Prediction (Split Conformal).
**Implementation**: Use a held-out calibration set ([deferred] of training data) to compute prediction intervals.
**Output**: Prediction interval [Lower, Upper] for every test prediction (Constitution Principle VII).

## Statistical Analysis Plan

### Performance Metrics
- **R², MAE, RMSE**: Calculated on the held-out test set for both models (FR-004).
- **Comparison**: Relative error reduction = `(MAE_baseline - MAE_gnn) / MAE_baseline`.
- **Success Criterion**: Improvement exceeds [deferred] relative error reduction target (SC-001).

### Power Analysis
**Method**: Post-hoc power analysis will be conducted to determine if the sample size (sufficient for final evaluation) is sufficient to detect the expected effect size (SC-001).
**Rationale**: Given the high dimensionality of graph features and the noise in yield data, a sample size may be underpowered to detect subtle GNN improvements. The plan explicitly acknowledges this limitation and will report effect sizes and confidence intervals rather than relying solely on p-values.

### Sensitivity Analysis (FR-005, SC-003)
- **Method**: Perturbation of input graph features to simulate experimental noise.
  - **Continuous Features**: Add Gaussian noise to continuous node features (e.g., electronegativity, partial charge).
  - **Categorical Features**: Apply discrete perturbation (e.g., randomly flip bond types with probability `p`) to ensure chemical validity.
  - **Exclusion**: Do NOT add noise to the target yield (tautological) or categorical identifiers (atomic number) directly.
- **Range**: Sweep noise levels over a range of values.
- **Metric**: Plot MAE vs. Noise Level.
- **Goal**: Assess robustness of GNN vs. Baseline to realistic experimental noise in molecular features.

### Attribution Analysis (FR-008)
- **Method**: GNNExplainer.
- **Target**: Identify top-ranked subgraph patterns (molecular fragments) contributing to high-yield predictions.
- **Output**: Ranked list of subgraphs with importance scores.
- **Validity Note**: GNNExplainer identifies features the *model uses* for prediction. Results are framed as "model attribution" and "predictive patterns," not as "causal drivers" of yield, to maintain construct validity.

### Multiple Comparison Correction
- **Method**: If multiple metrics or subgroups are tested, apply Bonferroni or Holm-Bonferroni correction.
- **Rationale**: To control Family-Wise Error Rate (Methodological Rigor).

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Dataset lacks yield data** | Fatal (No target variable) | Filter USPTO for non-null yield. If <10k samples, switch to MAESTRO or reduce scope. |
| **SMILES parsing failure >5%** | Blocking (FR-001) | Log errors, exclude invalid entries. If rate >10%, investigate dataset quality; consider alternative parser. |
| **OOM on CPU Runner** | Blocking (FR-006) | Reduce batch size, limit graph size, sample dataset to a large-scale collection of reactions. Use `torch.utils.data.DataLoader` with `num_workers=0`. |
| **GNN underperforms Baseline** | Null Result | Report honestly (US-003 Edge Case). Analyze if GNN is overfitting or if fingerprints capture yield better for this dataset. |
| **Runtime >10 hours** | Blocking (FR-006) | Monitor epochs. Use early stopping aggressively. Reduce hidden dimensions if needed. |
| **Underpowered Study** | Methodology Risk | Explicitly report power limits and effect sizes. Avoid overclaiming significance if sample size is insufficient. |

## Conclusion

The proposed plan addresses all functional requirements (FR-001 to FR-008) and success criteria (SC-001 to SC-005) within the strict CPU-only constraints. By leveraging verified USPTO-50k regression data, robust statistical methods (CV, Conformal Prediction), and a fair baseline comparison (including reaction-center descriptors), the project will deliver a reproducible assessment of GNN utility in reaction yield prediction.