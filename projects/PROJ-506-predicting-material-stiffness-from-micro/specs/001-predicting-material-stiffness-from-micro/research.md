# Research: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

## Dataset Strategy

Since this project relies on **synthetic data generation** rather than external datasets, no external dataset URLs are cited. The dataset is generated programmatically using `scikit-image` and validated via FFT-based numerical homogenization.

| Dataset Component | Source/Method | Verification Method |
|-------------------|---------------|---------------------|
| **Microstructure Images** | `scikit-image` procedural generation (stratified by density & topology) | Visual inspection + metadata validation (density, topology hash) |
| **Stiffness Ground Truth** | FFT-based numerical homogenization (custom `fft_homogenization.py`) | Comparison against Voigt-Reuss-Hill bounds (as sanity check only) |
| **Metadata** | Generated alongside images (density, tensor components, topology hash) | CSV/JSON schema validation |

**Note**: No external datasets are used. All data is synthetic and generated on-the-fly during the pipeline execution.

## Methodology

### 1. Synthetic Data Generation (FR-001) - **Stratified & Decoupled**
- **Approach**: Use `scikit-image` to generate 256x256 grayscale images.
- **Strategy**: **Decoupled Generation**. Generate samples by first fixing inclusion density (e.g., low, medium, and high levels) and then varying spatial topology (e.g., cluster size, connectivity, randomness) within each density bin.
- **Volume**: ≥ 2,000 samples to satisfy power analysis for 95% CI on MAE.
- **Validation**: Ensure that for a fixed density, the stiffness tensor varies significantly across different topologies. This prevents the model from learning a trivial density-to-stiffness mapping.

### 2. Ground Truth Calculation (FR-002)
- **Approach**: Implement FFT-based numerical homogenization to compute effective elastic stiffness tensors.
- **Rationale**: Analytical bounds (Voigt-Reuss-Hill) are insufficient as they ignore spatial topology. FFT captures the influence of inclusion arrangement on stiffness.
- **Validation**: All calculated tensors must fall within physically plausible bounds (Voigt-Reuss-Hill limits).
- **Constitution Note**: This method necessitates an amendment to Constitution Principle VI (from "analytical" to "FFT-based") to ensure scientific validity.

### 3. Model Architecture (FR-003) - **Ablation Study**
- **Architecture**: Shallow CNN with 3 convolutional layers, ReLU activation, and global average pooling.
- **Ablation Plan**: Before full training, run a small-scale ablation (a limited number of samples, 10 epochs) comparing 3-layer vs. 5-layer CNNs to verify the 3-layer model has sufficient receptive field for the generated microstructures.
- **Rationale**: Deep networks are computationally prohibitive on CPU-only runners. A shallow architecture balances expressiveness with runtime constraints, provided the ablation confirms sufficiency.
- **Compatibility**: Designed for CPU inference; no CUDA dependencies.

### 4. Training Strategy (FR-004, FR-005)
- **Optimizer**: Adam with learning rate scheduling.
- **Batch Size**: 32 (memory-constrained).
- **Epochs**: Max 50 (to stay within 6-hour runtime).
- **Cross-Validation**: 5-fold CV to assess stability and prevent overfitting.
- **Metrics**: MSE, R-squared, MAE.

### 5. Evaluation & Statistical Analysis (FR-006, FR-007, FR-008) - **ANOVA**
- **Binning**: Test data binned by inclusion density.
- **Statistical Tests**: **One-way ANOVA** (followed by Tukey HSD post-hoc tests) to compare prediction errors across density bins.
- **Correction**: Paired t-tests are invalid for independent groups (different microstructures). ANOVA is the correct test for comparing means across multiple independent groups.
- **Outlier Flagging**: Instances with MAE > 5% are flagged, especially those with densities outside the training distribution.
- **Generalization**: Quantify error degradation for out-of-distribution densities.

## Computational Feasibility

| Constraint | Mitigation Strategy |
|------------|---------------------|
| **No GPU** | Use CPU-only `torch`; avoid CUDA-specific operations. |
| **≤6 Hours** | Limit epochs to 50; use batch size 32; optimize FFT solver. |
| **~7 GB RAM** | Stream data in batches; avoid loading entire dataset into memory. |
| **Substantial Disk** | Compress generated images; clean intermediate files. |

## Assumptions & Limitations

- **Synthetic Representativeness**: Generated microstructures approximate real polymer microstructures sufficiently for surrogate training.
- **FFT Accuracy**: FFT-based homogenization provides accurate ground truth for 2D cases.
- **Topological Learnability**: Spatial arrangement of inclusions is learnable by a shallow CNN (verified via ablation).
- **Runtime Stability**: GitHub Actions runners are stable enough for extended jobs without preemption.
- **Constitution Amendment**: Principle VI is amended to allow FFT-based homogenization.

## References

- **FFT Homogenization**: Custom implementation based on standard numerical methods (no external URL cited).
- **Synthetic Generation**: `scikit-image` documentation (standard library).
- **CNN Architecture**: Standard shallow CNN designs for regression tasks.