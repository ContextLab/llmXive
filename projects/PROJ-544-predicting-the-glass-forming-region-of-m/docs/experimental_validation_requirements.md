# Experimental Validation Requirements

This document outlines the mandatory experimental confirmations required to validate the machine learning predictions of the glass-forming region for multi-component alloys.

While the computational pipeline computes descriptors (atomic size mismatch, mixing enthalpy, electronegativity variance) and predicts glass-forming ability (GFA) based on statistical correlations, these predictions remain associational. As noted in prior reviews (simulating Rosalind Franklin's perspective on structural determination vs. calculation), the distinction between amorphous and crystalline phases often depends on thermal history and cooling rates that cannot be inferred solely from static composition.

## 1. Primary Validation: X-Ray Diffraction (XRD)

**Requirement**: Every sample predicted to be a "glass" (amorphous) by the model must be confirmed via X-ray diffraction.

- **Criterion**: The XRD pattern must show a broad "halo" without sharp Bragg peaks characteristic of crystalline phases.
- **Minimum Sample Size**: A minimum of 10 experimentally confirmed glass samples is required to validate the model's positive predictive value.
- **Reference**: Comparison against standard patterns for the constituent elements and known intermetallic compounds in the system.
- **Traceability**: Each XRD dataset must be linked to the specific alloy composition ID used in the training/inference set.

## 2. Thermal History and Cooling Rate Verification

**Requirement**: The cooling rate used during sample fabrication must be documented and verified.

- **Context**: The glass-forming region is intrinsically linked to the cooling rate ($dT/dt$). A composition that forms a glass at $10^6$ K/s may crystallize at $10^2$ K/s.
- **Action**:
 - Record the specific cooling method (e.g., melt spinning, copper mold casting, splat quenching).
 - Estimate or measure the cooling rate for each sample.
 - Ensure the experimental cooling rate exceeds the critical cooling rate ($R_c$) predicted or observed for the system.
- **Constraint**: Samples produced via slow cooling (e.g., furnace cooling) must be excluded from the "glass" validation set unless the model explicitly accounts for low cooling rates (which it currently does not).

## 3. Differential Scanning Calorimetry (DSC)

**Requirement**: Thermal analysis to confirm the glass transition temperature ($T_g$) and crystallization temperature ($T_x$).

- **Criterion**: Observation of a distinct glass transition step followed by crystallization exotherms.
- **Metric**: Calculation of the supercooled liquid region $\Delta T_x = T_x - T_g$. A robust glass former typically exhibits a significant $\Delta T_x$.
- **Exclusion**: Samples showing only melting endotherms without a glass transition are classified as crystalline and must not be counted as false negatives if the model predicted "glass" (indicating a model failure to account for kinetics).

## 4. Microstructural Analysis (SEM/TEM)

**Requirement**: Scanning Electron Microscopy (SEM) or Transmission Electron Microscopy (TEM) for selected samples.

- **Purpose**: To rule out nanocrystalline structures that may appear amorphous in XRD due to peak broadening.
- **Criterion**: Homogeneous, featureless microstructure at the nanometer scale.
- **Action**: Perform selected area electron diffraction (SAED) in TEM to confirm the absence of diffraction spots.

## 5. Composition Verification

**Requirement**: Confirm the actual bulk composition matches the nominal stoichiometry.

- **Method**: Energy Dispersive X-ray Spectroscopy (EDS) or Inductively Coupled Plasma (ICP) analysis.
- **Tolerance**: Deviation from nominal composition must be within 1-2 at.% to ensure the input features (atomic size mismatch, etc.) are accurate.

## 6. Reproducibility Check

**Requirement**: Independent fabrication of at least 3 samples per predicted "glass" composition.

- **Purpose**: To ensure the glass formation is reproducible and not a result of a specific, non-repeatable processing anomaly.
- **Success Criteria**: All 3 samples must exhibit amorphous characteristics via XRD.

## 7. Negative Control Validation

**Requirement**: Confirm that samples predicted as "crystalline" are indeed crystalline.

- **Action**: Perform XRD on a subset of predicted crystalline samples.
- **Success Criteria**: Sharp Bragg peaks consistent with equilibrium or metastable intermetallic phases.

## Summary Checklist

- [ ] XRD patterns collected for all predicted glass samples (broad halo confirmation).
- [ ] Cooling rates documented and verified to be above critical $R_c$.
- [ ] DSC traces showing $T_g$ and $T_x$ for glass candidates.
- [ ] Bulk composition verified via EDS/ICP.
- [ ] Microstructural analysis (SEM/TEM) performed on ambiguous cases.
- [ ] Reproducibility confirmed for at least 3 samples per composition.
- [ ] Negative controls (predicted crystalline) confirmed via XRD.
- [ ] All data linked to specific sample IDs in the `data/derived/` directory.

## References

- Rosalind Franklin's work on DNA structural forms (A vs B) highlights the necessity of direct structural observation over calculation alone.
- Inoue, A. (2000). Stabilization of metallic supercooled liquid and bulk amorphous alloys. *Acta Materialia*.
- Johnson, W. L. (1999). Bulk glass-forming metallic alloys: Science and technology. *MRS Bulletin*.