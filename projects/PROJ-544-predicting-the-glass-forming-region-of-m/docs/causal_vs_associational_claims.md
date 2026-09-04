# Causal vs. Associational Claims in Glass-Forming Region Prediction

## Disclaimer

This document clarifies the nature of the predictive models developed in this project (PROJ-544). The machine learning models described herein identify **statistical associations** (correlations) between input features (atomic size mismatch, mixing enthalpy, electronegativity variance) and the target variable (glass-forming ability). They do **not** establish causal mechanisms.

## Nature of the Model

The core methodology relies on supervised learning algorithms (Random Forest, Gradient Boosting) trained on compositional data. These models learn a mapping function $f: X \rightarrow Y$ where $X$ represents the calculated descriptors and $Y$ represents the phase label (glass vs. crystalline).

- **Associational**: The model identifies that specific combinations of descriptors frequently co-occur with the glass phase in the training data.
- **Not Causal**: The model does not simulate the thermodynamic or kinetic pathways that lead to glass formation. It does not account for the underlying physical "why" unless explicitly encoded as a causal variable, which is not the case for these purely statistical descriptors.

## Reviewer Feedback: The Rosalind-Franklin-Simulated Critique

A critical review by the "rosalind-franklin-simulated" persona (dated 2026-05-14) highlighted a fundamental limitation in assuming these descriptors are primary drivers:

> "The model assumes atomic size mismatch and mixing enthalpy are the primary drivers of the glass-forming region. This is a statistical correlation, not a structural determination. In my work on DNA, the distinction between the A and B forms was not a matter of calculation, but of the hydration level observed in the fibre pattern. A change in water content shifts the unit cell parameters; similarly, the cooling rate and thermal history of these alloys must be measured, not merely inferred from atomic radii."

This feedback correctly identifies that:
1. **Missing Variables**: Critical physical parameters such as cooling rate, thermal history, and specific structural hydration (or analogous solvent/interstitial effects in alloys) are not captured by the current static compositional descriptors.
2. **Correlation vs. Mechanism**: High predictive accuracy on a test set does not imply the model has discovered the physical mechanism of glass formation. It may simply be exploiting a spurious correlation present in the training data distribution.
3. **Structural Determination**: True understanding of the glass-forming region requires structural data (e.g., XRD patterns, short-range order analysis) which is currently missing from the input features.

## Implications for Interpretation

When interpreting the results of this project, specifically the SHAP values and feature importance rankings:

- **Do not claim** that "Atomic Size Mismatch *causes* glass formation."
- **Do claim** that "Atomic Size Mismatch is a strong *predictor* of glass formation within the context of the available training data."

The model is a tool for **hypothesis generation** and **screening**, not a substitute for experimental validation of the physical mechanisms.

## Required Experimental Validation

To move from associational claims to causal understanding, the following experimental validations are necessary (see `docs/experimental_validation_requirements.md`):

1. **Controlled Cooling Rate Studies**: Verify if the predicted glass-forming region shifts when cooling rates are systematically varied.
2. **Structural Characterization**: Use X-ray Diffraction (XRD) and Transmission Electron Microscopy (TEM) to confirm the absence of long-range order in predicted glass samples.
3. **Thermal History Analysis**: Measure the thermal history of samples to ensure the model's predictions are not confounded by unrecorded processing conditions.

## Conclusion

The machine learning pipeline presented in this repository is a robust statistical engine for identifying potential glass-forming alloys based on compositional descriptors. However, users must recognize that these are **associational findings**. The "rosalind-franklin-simulated" critique serves as a vital reminder that without measuring the dynamic and structural variables (cooling rate, XRD patterns), the model remains a correlation engine, not a physics simulator. Future work must integrate these missing physical dimensions to establish causal links.