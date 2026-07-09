# Research: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

## 1. Problem Statement

The goal is to develop a surrogate model that predicts the effective elastic stiffness tensor of 2D microstructures from grayscale images. The challenge lies in capturing the non-linear relationship between the **spatial arrangement (topology)** of inclusions/voids and the resulting stiffness, which analytical bounds (Voigt-Reuss-Hill) fail to represent.

## 2. Dataset Strategy

### 2.1 Data Source
The project relies on **synthetic data generation** rather than external datasets.
- **Source**: Internal `code/data/generate_microstructures.py` using `scikit-image`.
- **Rationale**: No verified external dataset exists that provides both 2D microstructure images and corresponding FFT-based ground-truth stiffness tensors for the specific topology-dependent research question.
- **Dataset Size**: ≥ 2,000 images (128x128 pixels) to satisfy power analysis for 95% CI on MAE (FR-001).
 - *Note*: A feasible sample size exists under 6-hour CPU constraints. A post-hoc power analysis will be conducted to assess if this sample size is sufficient for the observed variance.

### 2.2 Verified Datasets (External)
*No external datasets are used for training or validation. The following verified datasets were reviewed but deemed unsuitable:*
- **CPU-only (parquet)**: ` (Text-only, irrelevant).
- **CNN (parquet)**: ` (Text summarization, irrelevant).
- **MAE (zip)**: ` (Audio/MIDI, irrelevant).

**Decision**: Synthetic generation is the only viable path to ensure ground truth accuracy and topology dependence.

### 2.3 Data Generation Methodology
1. **Microstructure Generation**: Randomized void/inclusion densities and spatial distributions using `scikit-image`.
 - **Topological Diversity**: The generator will use **Latin Hypercube Sampling (LHS)** to vary spatial correlation length and clustering parameters **independently** of volume fraction. This ensures that for any given density, the dataset contains a diverse range of topologies (e.g., clustered, dispersed, percolated), preventing the model from learning a simple density-stiffness mapping.
2. **Ground Truth Calculation**: FFT-based numerical homogenization (using `scipy.fft` or `pyfftw`) to compute effective stiffness tensors.
 - **Method**: Solve the Lippmann-Schwinger equation via FFT.
 - **Ground Truth Definition**: The **exact numerical value** produced by the FFT solver is the target label. **Crucially**, the model is **not** trained to predict Voigt-Reuss-Hill (VRH) bounds. VRH is used **only** as a plausibility filter to discard numerically unstable simulations.
 - **Physical Plausibility Check**: Values are checked against VRH bounds. If a value is within VRH bounds but the FFT solver failed to converge, it is discarded. If a value is outside VRH bounds, it is discarded as physically invalid.
 - **Constraint**: Handle convergence failures for extreme densities (>90% voids) by flagging and excluding from training.

## 3. Model Architecture & Training

### 3.1 Architecture
- **Type**: Shallow Convolutional Neural Network (CNN).
- **Layers**: 2-3 Convolutional layers (3x3 kernels), ReLU activation, Global Average Pooling.
- **Output**: 6 values (representing the 2D stiffness tensor components: $C_{11}, C_{12}, C_{22}, C_{66}$, etc., depending on symmetry).
- **Rationale**: Deep networks are unnecessary for this correlation and would violate CPU runtime constraints (FR-003).

### 3.2 Training Configuration
- **Framework**: PyTorch (CPU mode).
- **Optimizer**: Adam.
- **Batch Size**: 32.
- **Epochs**: Max 50.
- **Loss Function**: Mean Squared Error (MSE) against the **exact FFT numerical values**.
- **Hardware**: 2-core CPU, ~7 GB RAM (GitHub Actions free tier).
- **Feasibility**: Estimated training time < 4 hours for [deferred] samples and 50 epochs on CPU (using 128x128 images).

### 3.3 Validation Strategy
- **K-Fold Cross-Validation**: 5-fold to assess stability (FR-005).
 - **Stratification**: Folds will be stratified by both **inclusion density** and **topological features** (e.g., clustering coefficient) to ensure the model cannot simply learn density-stiffness correlations.
- **Metrics**: MSE, R-squared, MAE (FR-006).
- **Target**: MAE ≤ 5% relative to ground truth (SC-001).

## 4. Statistical Analysis & Generalization

### 4.1 Generalization Testing
- **Method**: Bin test data by inclusion density (e.g., 0-20%, 20-40%,..., 80-100%).
- **Metric**: Compare prediction errors across bins.
- **Hypothesis**: Error increases for densities outside the training distribution (SC-002).

### 4.2 Statistical Tests
- **Test**: Paired t-tests on prediction errors between density bins.
- **Significance**: p-value < 0.05 (SC-004).
- **Outlier Flagging**: Flag instances where MAE > 5% (FR-008) to identify failure modes.

### 4.3 Limitations
- **Dataset**: Synthetic data may not perfectly represent real-world polymer microstructures (Assumption 1).
- **2D Representation**: 3D effects are ignored; results are specific to 2D slices.
- **CPU Constraints**: Model complexity is limited by runtime; deeper architectures not explored.
- **Sample Size**: [deferred] samples is a minimum baseline. High variance in MAE may limit the precision of the absolute error estimate, but the *relative* trends across density bins remain valid.

## 5. Constitution Amendment Proposal

**Current Principle VI**: "The project generates labels using analytical homogenization formulas..."
**Proposed Amendment**: "The project generates labels using FFT-based numerical homogenization. The validity of the surrogate model depends on the accuracy of these numerical solutions for the specific microstructure topology."
**Justification**: Analytical bounds (Voigt-Reuss-Hill) are topology-independent. Using them would make the CNN task trivial (predicting a function of volume fraction only) and fail to answer the research question regarding spatial arrangement. FFT-based homogenization is the standard method for topology-dependent effective properties.

**Action Plan**:
1. Draft `docs/constitution_amendment_proposal.md`.
2. Update `constitution.md` (Principle VI) prior to data generation.
3. Record the change in `state/` files.
