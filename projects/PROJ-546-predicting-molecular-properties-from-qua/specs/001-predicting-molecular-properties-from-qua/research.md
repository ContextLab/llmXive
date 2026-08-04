# Research Question Validation

## Objective
Validate whether semi-empirical quantum chemical calculations (DFTB+) can serve as a computationally efficient proxy for high-level DFT (B3LYP) in predicting molecular reaction barriers.

## Hypothesis
Machine learning models trained on DFTB+ descriptors will achieve a Mean Absolute Error (MAE) within 2.0 kcal/mol of experimental values, comparable to models trained on DFT descriptors, while reducing computational cost by an order of magnitude.

## Methodology
1. **Data Acquisition**: Download experimental barrier dataset from Zenodo.
2. **Descriptor Generation**:
 - Run DFTB+ for geometry optimization and descriptor extraction on the full dataset.
 - Run Psi4 (B3LYP/def2-SVP) on a stratified subset (50 molecules) using the *same* optimized geometries from DFTB+.
3. **Model Training**: Train Random Forest regressors on both descriptor sets.
4. **Evaluation**: Compare MAE against experimental ground truth using 5-fold CV and paired t-tests.
5. **Sensitivity Analysis**: Analyze feature importance and stability across descriptor thresholds.

## Physical Constraints
- **Constitution Principle VI**: Geometries for DFT must match DFTB+ to ensure fair comparison.
- **Physical Reality**: Descriptors must satisfy `HOMO < LUMO` and charge conservation.
