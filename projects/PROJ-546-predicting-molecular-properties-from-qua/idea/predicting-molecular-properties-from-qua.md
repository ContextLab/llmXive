# Idea: Predicting Molecular Properties from Quantum Chemical Calculations

## Motivation
Predicting molecular reaction barrier heights is critical for drug discovery and materials science. High-level DFT methods are accurate but computationally expensive. Semi-empirical methods (DFTB+) are fast but less accurate. This project aims to bridge the gap by using machine learning to predict DFT-level accuracy from semi-empirical descriptors.

## Approach
1. **Data Collection**: Download experimental barrier dataset from Zenodo.
2. **Descriptor Generation**:
 - Compute semi-empirical descriptors (HOMO, LUMO, Mayer) using DFTB+ on full dataset.
 - Compute high-level DFT descriptors on a stratified subset using Psi4.
3. **Model Training**: Train Random Forest models on semi-empirical and DFT descriptors.
4. **Evaluation**: Compare MAE of both models against experimental ground truth.
5. **Sensitivity Analysis**: Identify top descriptors and analyze threshold effects.

## Expected Outcomes
- A pipeline that generates descriptors from quantum calculations.
- Two trained models (semi-empirical vs DFT) with comparative metrics.
- Insights into which descriptors are most predictive of barrier heights.
- Evidence of physical interpretability (top descriptors map to chemical properties).

## Challenges
- **Convergence**: DFTB+ may fail to converge for some molecules.
- **Cost**: DFT calculations are expensive; subset selection is critical.
- **Accuracy**: Semi-empirical methods may not capture all physical effects.

## Validation
- Compare model predictions against experimental data.
- Verify physical ranges (HOMO < LUMO, reasonable energies).
- Ensure reproducibility via checksums and versioned dependencies.
