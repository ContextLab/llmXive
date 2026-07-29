# Research Question Validation

## Context
Predicting molecular barrier heights is a critical task in computational chemistry.
High-level DFT methods (e.g., B3LYP) are accurate but computationally expensive.
Semi-empirical methods (e.g., DFTB+) are faster but less accurate.

## Hypothesis
A Random Forest model trained on semi-empirical descriptors can predict barrier heights with sufficient accuracy (MAE < 2.0 kcal/mol) to be a viable alternative for large-scale screening, provided the speedup is >10x.

## Methodology
1. **Data Collection**: Fetch experimental barrier data from Zenodo.
2. **Descriptor Generation**:
 - Run DFTB+ on full dataset for semi-empirical descriptors.
 - Run Psi4 on a subset for high-level DFT descriptors.
3. **Model Training**: Train Random Forest models on both datasets.
4. **Evaluation**: Compare MAE and statistical significance.
5. **Analysis**: Identify key descriptors and sensitivity to thresholds.

## Validation Criteria
- **Accuracy**: Semi-empirical MAE must be within 2.0 kcal/mol of experimental values.
- **Efficiency**: Semi-empirical workflow must be >10x faster than DFT.
- **Robustness**: Pipeline must handle convergence failures and OOM errors gracefully.

## Limitations
- DFTB+ accuracy depends on the parameter set used.
- DFT calculations are limited to a subset due to computational cost.
- Geometry optimization protocols differ between DFTB+ and DFT.
