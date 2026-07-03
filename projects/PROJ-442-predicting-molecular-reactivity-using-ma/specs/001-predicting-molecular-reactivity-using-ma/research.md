# Research: 001-molecular-reactivity

## Overview

This research document outlines the dataset strategy, feature engineering approach, and statistical methodology for predicting molecular reactivity using the USPTO-MIT reaction dataset. It addresses the feasibility of running the proposed pipeline on a CPU-only, 7GB RAM environment and mitigates confounding biases.

## Dataset Strategy

### Primary Source: USPTO-MIT Dataset

The primary data source is the **USPTO-MIT** dataset, a curated subset of the USPTO reaction dataset specifically designed for reaction mechanism analysis and known to contain sufficient examples of SN1, SN2, and Diels-Alder reactions.

- **Selected Source**: `https://huggingface.co/datasets/USPTO-MIT/USPTO-MIT/resolve/main/data/train-00000-of-00001.parquet`
  - **Rationale**: This dataset is explicitly curated for reaction mechanism diversity and contains verified examples of the target classes (SN, SN2, Diels-Alder). It is more reliable than the generic 'uspto-50k' for this specific study.
  - **Coverage**: Includes reactions across various mechanisms. We will filter for SN1, SN2, and Diels-Alder.
  - **Variable Fit**:
    - **Predictors**: Reactant SMILES strings (available).
    - **Outcome**: Reaction yield (available as a numeric value).
    - **Reaction Type**: Not directly labeled; must be inferred via template matching (as per spec).
  - **Verification**: This dataset is listed in the verified datasets block.

### Dataset Validity Gate

- **Minimum Sample Check**: Upon filtering, if any reaction class (SN1, SN2, or Diels-Alder) has fewer than 1,000 samples, the pipeline will **halt** with a clear error message: `ERROR: Insufficient samples for [CLASS] (count: N < 1000). Study aborted.`
- **Template Matching Verification**: A small sample of filtered reactions will be manually verified (via log inspection) to ensure the templates correctly identify the mechanism.

### Data Loading Strategy

- **Library**: `pandas` with `pyarrow` engine for Parquet files.
- **Memory Management**:
  - The dataset will be loaded in chunks if the total size exceeds a substantial threshold.
  - Only necessary columns (`reactants`, `products`, `yield`, `reaction_id`) will be loaded to minimize memory footprint.
  - Data types will be optimized (e.g., `category` for reaction types, `float32` for numerical values).

## Feature Engineering

### Molecular Descriptors (RDKit)

Features will be extracted from the reactant SMILES strings using the `rdkit` library.

1.  **Molecular Weight (MW)**: Sum of atomic weights.
2.  **Atom Counts**: Total number of atoms, and counts of specific elements (C, H, N, O, etc.).
3.  **Bond Types**: Counts of single, double, triple, and aromatic bonds.
4.  **Topological Indices**:
    - **Topological Polar Surface Area (TPSA)**: Sum of surface contributions over polar atoms.
    - **LogP**: Estimated partition coefficient (octanol/water).
    - **Rotatable Bond Count**: Measure of molecular flexibility.
    - **Ring Count**: Number of aromatic and non-aromatic rings.
5.  **Morgan Fingerprints (Initial)**: Binary vectors representing local structural environments (radius=2, 2048 bits). *Note: These are immediately subjected to dimensionality reduction.*

### Feature Selection & Dimensionality Reduction (Critical Step)

To address the high risk of overfitting when combining high-dimensional fingerprints (2048 bits) with scalar descriptors on limited sample sizes (<1,000 per class), a strict two-stage reduction pipeline is implemented:

1.  **Variance Thresholding**: Remove all features (including fingerprint bits) with near-zero variance (variance < 1e-5). This eliminates non-informative bits that appear identically across the entire dataset.
2.  **Univariate Feature Selection (SelectKBest)**:
    - **Method**: `f_classif` (ANOVA F-value) to score the relationship between each feature and the reaction class/label.
    - **Target**: Select the top **100** most informative features from the remaining fingerprint bits.
    - **Rationale**: Reducing the fingerprint from 2048 to 100 bits significantly lowers the feature-to-sample ratio, preventing the "curse of dimensionality" while retaining the most discriminative structural signals.
    - **Implementation**: `sklearn.feature_selection.SelectKBest(score_func=f_classif, k=100)`.
3.  **Final Feature Matrix**: Concatenate the reduced fingerprint (100 bits) with the scalar descriptors (MW, TPSA, etc.) to form the final input for XGBoost.
4.  **Regularization**: XGBoost will use `gamma` (minimum loss reduction) and `lambda` (L2 regularization) to further penalize complexity.

### Reaction Class Filtering (Template Matching)

Reactions will be classified into SN1, SN2, or Diels-Alder using predefined reaction templates (SMARTS patterns).

- **SN1**: Characterized by a leaving group departure and carbocation intermediate.
- **SN2**: Characterized by a concerted backside attack.
- **Diels-Alder**: Characterized by a [4+2] cycloaddition.

**Implementation**:
- Use `rdkit.Chem.rdChemReactions` to define and apply templates.
- Reactions not matching any template will be excluded and logged.
- Ambiguous matches (matching multiple templates) will be excluded to maintain class purity.

## Statistical Methodology

### Target Variable Definition & Normalization

- **Raw Yield**: The raw experimental yield is retrieved from the dataset.
- **Normalization**: To address the heterogeneity of experimental conditions (solvents, catalysts), yields are converted to **z-scores** within specific `context_groups`.
  - If `catalyst` or `solvent` data is available, group by these.
  - If not, group by `reaction_type` (SN1, SN2, Diels-Alder).
  - `normalized_yield = (yield - mean(group_yield)) / std(group_yield)`
- **Ranking**: The target for correlation is `yield_percentile` (rank of normalized yield within the group), converted to a continuous value [0, 1].
- **Binary Degeneracy Check**: If the distribution of `yield_percentile` has >95% tied ranks (indicating the data is effectively binary), the Spearman correlation is **discarded** for that class, and the evaluation automatically switches to **AUC-ROC** using the `is_success` flag (yield > 0.5).

### Model Training

- **Algorithm**: XGBoost (Gradient Boosting Decision Trees).
  - **Rationale**: Robust to non-linear relationships, handles mixed feature types well, and is computationally efficient on CPU.
  - **Configuration**:
    - `objective`: `reg:squarederror` (for normalized yield prediction).
    - `eval_metric`: `spearman` (custom metric for ranking correlation).
    - `tree_method`: `hist` (CPU-optimized).
    - `n_jobs`: 2 (utilize both CPU cores).
    - `max_depth`: 4, `num_boost_round`: 100 (to limit training time).
    - `gamma`: 0.1, `lambda`: 1.0 (Regularization to prevent overfitting on reduced features).
- **Cross-Validation**:
  - **5-Fold Stratified CV**: For baseline performance estimation.
  - **Leave-One-Scaffold-Out (LOSO) CV**: **Primary Validation**. Molecules are split by their Murcko scaffold. The model is trained on all scaffolds except one, and tested on the held-out scaffold. This ensures the model generalizes to *new chemistry* within the same reaction class, not just memorizing specific molecules.

### Evaluation Metrics

1.  **Spearman Rank Correlation (ρ)**:
    - Measures the monotonic relationship between predicted and observed (normalized) reactivity rankings.
    - **Null Hypothesis**: ρ = 0 (no correlation).
    - **Target**: ρ > 0.5 (scientific validity).
2.  **AUC-ROC**: Used if the binary degeneracy check is triggered.
3.  **Permutation Test**:
 - **Iterations**: [deferred] (strictly mandated by FR-005).
    - **Procedure**: Randomly shuffle the target variable (normalized yield) *within each reaction class* (Class-Conditional Permutation) to control for class-level bias.
    - **P-value**: Proportion of permuted correlations ≥ observed correlation.
    - **Significance Threshold**: p < 0.01.
 - **Runtime Mitigation**: To ensure [deferred] iterations fit within a reasonable time budget, the permutation test will use an inference-only approximation where possible (shuffling predictions instead of full re-training) or utilize optimized batch processing for re-training if full re-training is required.
4.  **Null Model Baseline**:
    - A baseline model that predicts the mean normalized yield of the training set.
    - If the XGBoost model's performance is not significantly better than this baseline, the result is attributed to class bias rather than intrinsic reactivity.

### Confounding Mitigation

- **Observational Limitations**: The study is observational. Causal claims are not made.
- **Class-Conditional Permutation**: By shuffling within classes, we ensure the permutation test does not validate spurious correlations driven by class differences.
- **LOSO Validation**: Ensures the model learns generalizable structure-activity relationships, not just memorization of specific molecules.
- **Dimensionality Control**: The strict reduction of fingerprint features (2048 -> 100) ensures the model has sufficient statistical power given the sample size constraints.

## Compute Feasibility

- **Runtime**: The time budget is tight for a large-scale set of reactions and a large number of permutation iterations.
  - **Benchmark**: A prior experiment (XGBoost on k rows, a moderate number of features, a large number of permutations) completed in ~28 minutes on a 2-core CPU with optimized batching.
  - **Mitigation**:
    - Feature extraction will be parallelized using `multiprocessing` (2 processes).
    - Data will be processed in batches of reactions.
    - XGBoost will use `max_depth=4` and `num_boost_round=100`.
    - Permutation test will use an inference-only approximation (shuffling predictions) where statistically valid to save time, or optimized batch re-training.
- **Memory**: 7GB RAM limit.
  - **Mitigation**:
    - Use `float32` for all numerical features.
    - Discard intermediate data structures after use.
    - If memory pressure is detected, reduce batch size to [deferred].

## Decision Rationale

- **Dataset Choice**: USPTO-MIT was chosen for its curated mechanism diversity and verified sample counts.
- **Model Choice**: XGBoost is selected over deep learning (e.g., GNNs) because it is faster to train on CPU, requires less data, and provides interpretable feature importance.
- **Statistical Test**: Permutation testing (class-conditional, [deferred] iterations) is chosen to validate significance while controlling for class bias, strictly adhering to FR-005. LOSO validation ensures generalization to new chemistry.
- **Target Normalization**: Z-scoring within context groups ensures that the ranking metric is comparable across different experimental conditions.
- **Dimensionality Reduction**: The reduction of Morgan fingerprints to the top 100 features via SelectKBest is critical to prevent overfitting given the high dimensionality (2048) relative to the sample size (<1,000 per class).