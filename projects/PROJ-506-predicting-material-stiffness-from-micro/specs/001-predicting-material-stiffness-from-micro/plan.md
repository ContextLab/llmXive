# Project Plan: Predicting Material Stiffness from Microstructure Images

## 1. Overview
This plan outlines the execution strategy for developing a CNN-based predictor for material stiffness.

## 2. Phases

### Phase 0: Governance & Constitution
- **Task 0.1**: Amend Constitution to allow FFT-based homogenization.
- **Task 0.2**: Update State files to reflect governance changes.
- **Task 0.3**: Update Specification to reflect resolution changes (128x128).
- **Task 0.4**: Update Specification and Plan to reflect statistical method changes (ANOVA).

### Phase 1: Setup
- Initialize project structure, dependencies, and linting.

### Phase 2: Foundational
- Implement FFT homogenization solver.
- Implement metrics and k-fold utilities.
- Define schema contracts.

### Phase 3: User Story 1 (Data Generation)
- Generate microstructures and compute ground truth.

### Phase 4: User Story 2 (Training)
- Train CNN model with cross-validation.

### Phase 5: User Story 3 (Evaluation)
- Evaluate generalization and perform statistical analysis.

## 3. Methodology

### 3.1 Data Generation
- Use `scikit-image` to generate binary microstructures.
- Use FFT-based homogenization (CPU) for ground truth stiffness.

### 3.2 Model Training
- PyTorch CPU backend.
- Stratified K-Fold cross-validation (stratified by density and topology).

### 3.3 Statistical Test
- **Primary Method**: One-way Analysis of Variance (ANOVA).
- **Post-hoc**: Tukey's Honestly Significant Difference (HSD) test.
- **Rationale**: The dataset contains multiple density bins (>2 groups). A paired t-test is inappropriate for comparing means across multiple independent groups. One-way ANOVA determines if at least one group mean is statistically different, and Tukey HSD identifies which pairs differ.
- **Implementation**: Use `scipy.stats.f_oneway` and `statsmodels` for Tukey HSD.
- **Note**: This methodology supersedes any previous references to "paired t-tests" in this document or the specification.

### 3.4 Success Criteria
- **SC-001**: MAE < 5%.
- **SC-002**: Quantified OOD degradation.
- **SC-003**: Runtime < 6 hours.
- **SC-004**: **One-way ANOVA** p-value < 0.05 on error distribution across density bins.
- **SC-005**: R2 stability (std < 0.05).

## 4. Risk Management
- **Risk**: CPU convergence of FFT solver.
- **Mitigation**: Use `pyfftw` for optimized FFT operations.
- **Risk**: Statistical power.
- **Mitigation**: Ensure sufficient sample size per density bin for ANOVA validity.

## 5. Deliverables
- `data/raw/`: Generated microstructures and metadata.
- `data/processed/`: Analysis reports, ANOVA tables, degradation plots.
- `code/models/`: Trained model weights.
- `docs/`: Final report and API documentation.