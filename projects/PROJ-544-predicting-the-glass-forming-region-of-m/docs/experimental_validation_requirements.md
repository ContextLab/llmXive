# Experimental Validation Requirements

This document outlines the mandatory experimental validation steps required to substantiate the machine learning predictions of the glass-forming region for multi-component alloys. While the computational model provides statistical correlations based on atomic size mismatch, mixing enthalpy, and electronegativity variance, these metrics are insufficient to confirm the formation of a glassy phase without direct structural evidence.

## 1. Primary Validation: X-Ray Diffraction (XRD)

The definitive method for distinguishing between amorphous (glassy) and crystalline phases is X-ray Diffraction.

### 1.1 Required Data Points
For every alloy composition predicted to be in the "glass-forming region" with high confidence, the following must be provided:
- **XRD Pattern**: A full diffraction scan (2θ range typically 10°–90°) using Cu Kα radiation.
- **Peak Analysis**:
 - **Glassy Phase**: Confirmation of the absence of sharp Bragg peaks. The presence of broad, diffuse halos centered around typical metallic diffraction angles (e.g., ~40°–50° 2θ) is the signature of amorphous structure.
 - **Crystalline Phase**: Identification of sharp, narrow peaks indicating long-range order.
- **Crystallinity Fraction**: Quantification of the amorphous fraction (e.g., >95% amorphous) via Rietveld refinement or peak area integration.

### 1.2 Rejection of Inferential Methods
As noted in the review by rosalind-franklin-simulated, statistical correlation of thermodynamic descriptors does not equate to structural determination. Just as the distinction between DNA A and B forms relies on hydration levels observed in fibre patterns rather than calculation, the glass transition in alloys relies on thermal history and cooling rates that cannot be fully inferred from static atomic properties.
- **No XRD = No Validation**: Predictions lacking XRD confirmation are classified as `experimental_validation_status: unknown` in the data contracts.
- **No DSC-only Validation**: Differential Scanning Calorimetry (DSC) showing a glass transition temperature ($T_g$) is supportive but secondary. A material may exhibit a $T_g$ without being fully amorphous, or may crystallize during the DSC scan. XRD is the primary arbiter.

## 2. Thermal History and Cooling Rate Verification

The glass-forming ability (GFA) is intrinsically linked to the cooling rate ($R_c$) used during synthesis.

- **Minimum Cooling Rate**: The synthesis protocol must document the cooling rate (e.g., melt spinning at >10^5 K/s, copper mold casting, arc melting).
- **Thermal Stability**: Measurement of the supercooled liquid region ($\Delta T_x = T_x - T_g$) via DSC to confirm thermal stability consistent with bulk metallic glasses (BMGs).
- **Critical Diameter**: For bulk glass formers, the critical casting diameter ($D_{max}$) must be measured to verify the depth of the glass-forming region.

## 3. Compositional Homogeneity

- **EDS/WDS Mapping**: Energy-Dispersive X-ray Spectroscopy (EDS) or Wavelength-Dispersive X-ray Spectroscopy (WDS) mapping must confirm that the bulk composition matches the intended stoichiometry and that no phase segregation (e.g., dendritic crystalline phases) occurred during solidification.

## 4. Data Submission Format

Experimental results must be submitted in the following format to be considered for model retraining:
- `sample_id`: Unique identifier linking to the `data/derived/descriptor_vector.csv`.
- `xrd_file`: Raw `.raw` or `.xy` file of the diffraction pattern.
- `thermal_history`: JSON object containing cooling rate, annealing temperature, and quench medium.
- `validation_status`: Enum (`confirmed_glass`, `confirmed_crystalline`, `mixed_phase`, `inconclusive`).

## 5. Failure Mode Analysis

If a sample predicted to be a glass is found to be crystalline via XRD:
1. The sample must be re-analyzed for potential impurities or segregation.
2. The discrepancy must be logged in `logs/model_accuracy_issue.log` with the `experimental_validation_status` flag set to `no`.
3. The feature importance analysis (SHAP) must be reviewed to determine if the model over-relied on a specific descriptor (e.g., atomic size mismatch) that does not account for kinetic factors like nucleation barriers.

## Conclusion

The ML model serves as a screening tool to prioritize compositions for experimental synthesis. However, the claim of "predicting the glass-forming region" is only valid when the predicted region is populated by samples with verified XRD patterns confirming the amorphous state. Without this experimental anchor, the model remains a correlational exercise rather than a predictive scientific tool.