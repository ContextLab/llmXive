# Research Question Validation

## Primary Question
Can semi-empirical quantum chemical descriptors (DFTB+) be used to predict molecular reaction barrier heights with accuracy comparable to high-level DFT (Psi4), while reducing computational cost?

## Sub-Questions
1. **Descriptor Quality**: Do HOMO, LUMO, and Mayer bond order from DFTB+ correlate with experimental barrier heights?
2. **Model Performance**: How does the MAE of a Random Forest model trained on DFTB+ descriptors compare to one trained on DFT descriptors?
3. **Physical Interpretability**: Do the top features identified by the model correspond to known chemical properties (e.g., electronegativity, bond order)?
4. **Stability**: Are the top descriptors stable across different threshold sweeps?

## Hypotheses
- **H1**: DFTB+ descriptors will show significant correlation with experimental barriers, but with higher MAE than DFT descriptors.
- **H2**: The difference in MAE between DFTB+ and DFT models will be within 2.0 kcal/mol (acceptable threshold).
- **H3**: Top features will map to physical mechanisms (e.g., frontier orbital energies, bond strength).

## Validation Strategy
- **Statistical**: Paired t-test to compare MAE of DFTB+ and DFT models.
- **Physical**: Map top features to chemical properties using domain knowledge.
- **Robustness**: Sensitivity analysis over descriptor thresholds.

## Limitations
- **Dataset Size**: Limited by availability of experimental data.
- **Computational Cost**: DFT calculations restricted to a subset.
- **Method Approximations**: DFTB+ and DFT both have inherent approximations.

## Conclusion
This research will provide evidence on the trade-off between computational cost and accuracy in predicting molecular properties. If successful, it could enable large-scale screening using semi-empirical methods with ML correction.