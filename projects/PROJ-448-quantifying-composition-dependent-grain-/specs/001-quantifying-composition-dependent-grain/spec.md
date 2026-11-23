# Feature Specification: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Feature Branch**: `001-quantifying-grain-boundary-segregation`  
**Created**: 2026-06-13  
**Status**: Draft  
**Input**: User description: "Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1)

As a materials researcher, I want to compute equilibrium segregation energies and concentrations for specific BCC alloy systems (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, Fe-Mo-W) at defined temperatures using DFT-derived segregation energies and the McLean isotherm model, so that I can establish the baseline thermodynamic relationship between bulk composition and grain boundary chemistry.

**Why this priority**: This is the core scientific engine of the project. Without accurate segregation profiles derived from first principles and validated thermodynamic models, no further analysis of non-linearities or cooperative effects is possible. It delivers the primary dataset required for the research question.

**Independent Test**: Can be fully tested by running the computation pipeline on a single binary system (e.g., Fe-Cr) at a single temperature (e.g., 700K) and verifying that the output file is generated correctly and the McLean equation is applied algebraically using the provided DFT energy input. This is a pipeline sanity check to ensure the code executes without error; scientific validation of the DFT physics against experimental data is performed separately in SC-003.

**Acceptance Scenarios**:

1. **Given** a valid CALPHAD database file and a pre-built BCC grain boundary supercell model for Fe-Cr, **When** the system executes the DFT energy extraction and McLean isotherm calculation at 700K, **Then** the output file contains a segregation energy value (derived from DFT) and an equilibrium concentration (derived from McLean using that energy) with units of eV and atomic fraction respectively.
2. **Given** a bulk concentration of 0.05 for Cr, **When** the system computes the segregation profile, **Then** the resulting equilibrium concentration at the grain boundary is higher than the bulk concentration (positive segregation) if the segregation energy is negative, consistent with thermodynamic theory.
3. **Given** an invalid or missing supercell model file, **When** the system attempts the calculation, **Then** the process terminates with a clear error message identifying the missing dependency and does not produce a partial or corrupted output file.
4. **Given** a valid TCFE9 CALPHAD database URL, **When** the system executes the retrieval step, **Then** the system downloads the file, verifies its checksum against the provided hash, and logs a success message before proceeding.

---

### User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

As a materials researcher, I want to analyze the computed segregation profiles across ternary alloy systems to identify non-linear thresholds and cooperative effects where the presence of multiple solutes amplifies segregation beyond single-element predictions, so that I can determine if current linear models are insufficient for alloy design.

**Why this priority**: This addresses the specific research gap regarding "cooperative effects" mentioned in the motivation. It moves beyond simple binary analysis to the complex multicomponent behavior that is critical for modern alloy design, providing the "publishable evidence" of non-linearity.

**Independent Test**: Can be fully tested by running the analysis on the pre-computed ternary dataset (Fe-Cr-Mo, etc.) and verifying that the regression model with interaction terms identifies at least one statistically significant interaction coefficient (p<0.05) and demonstrates a >10% reduction in Mean Squared Error (MSE) on a held-out test set compared to a purely additive binary model.

**Acceptance Scenarios**:

1. **Given** the computed segregation energies for Fe-Cr-Mo across the 500-900K range, **When** the system fits a regression model including interaction terms, **Then** the output includes a coefficient for the Cr-Mo interaction term and a p-value indicating statistical significance if a cooperative effect exists.
2. **Given** a heatmap visualization of segregation energy vs. bulk composition, **When** the researcher inspects the plot, **Then** distinct regions of high segregation are visible that cannot be explained by the sum of binary contributions alone.
3. **Given** a dataset where all interaction terms are zero, **When** the system runs the analysis, **Then** the output explicitly states that no significant cooperative effects were detected within the statistical power of the current sample.

---

### User Story 3 - Model Generalizability and Cross-Validation (Priority: P3)

As a materials researcher, I want to perform k-fold cross-validation (k=5) on the empirical composition-segregation functions across the combined dataset of all alloy systems, so that I can assess the robustness and generalizability of the derived relationships before applying them to new alloy designs.

**Why this priority**: This ensures the scientific validity and reproducibility of the findings. It validates that the observed relationships are not artifacts of a specific dataset but represent general physical principles, which is essential for the "rational alloy design" goal.

**Independent Test**: Can be fully tested by executing the cross-validation routine on the existing dataset (split by composition and temperature points, not by system) and verifying that the reported mean squared error (MSE) or R-squared metric remains stable across the 5 folds, with a standard deviation below a defined threshold (e.g., 0.05).

**Acceptance Scenarios**:

1. **Given** a fitted empirical model for the Fe-Cr-Mo system, **When** the system performs 5-fold cross-validation on the composition/temperature data points, **Then** the output includes the performance metric (e.g., R²) for each of the 5 folds and the overall mean and standard deviation.
2. **Given** a model trained on Fe-Cr-Mo data, **When** it is tested on a held-out subset of Fe-Cr-V data (if applicable), **Then** the prediction error is reported to assess transferability between systems.
3. **Given** a scenario where the model overfits (high training accuracy, low validation accuracy), **When** the cross-validation is run, **Then** the system flags the high variance between training and validation scores, suggesting the model is not generalizable.

### Edge Cases

- What happens when the CALPHAD database does not contain a specific ternary interaction parameter required for a temperature in the 500-900K range? (System should extrapolate with a warning or flag the data gap).
- How does the system handle DFT convergence failures for specific grain boundary supercells? (System should retry up to 3 times, modifying the 'mixing_beta' parameter by 0.1 increments and increasing 'ecutwfc' by [deferred] per retry, then log the failure and exclude the data point from the analysis).
- What occurs if the McLean isotherm calculation results in a concentration > 1.0 (physically impossible)? (System should cap the value at 1.0 and log a "saturation" flag for review).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract equilibrium phase compositions for Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, and Fe-Mo-W ternary systems at temperatures between 500K and 900K from the provided CALPHAD database files. (See US-1)
- **FR-002**: System MUST compute segregation energies using the Quantum ESPRESSO DFT code on BCC grain boundary supercell models generated deterministically using the `pymatgen` library. The system MUST use a Materials Project bulk lattice ID for BCC Fe as the seed and generate a Σ symmetric tilt grain boundary supercell. (See US-1)
- **FR-003**: System MUST calculate equilibrium segregation profiles using the McLean isotherm model, using the DFT-derived segregation energy as the primary input parameter to predict grain boundary concentration. (See US-1)
- **FR-004**: System MUST fit empirical composition-segregation functions using linear regression with interaction terms. The system MUST compare the predictive power (MSE) of this model against a null hypothesis (purely additive binary model) on a held-out test set, requiring a >10% MSE reduction to confirm cooperative effects. (See US-2)
- **FR-005**: System MUST perform 5-fold cross-validation on the combined dataset of composition and temperature points across all alloy systems to assess model generalizability and report performance metrics. (See US-3)
- **FR-006**: System MUST generate heatmaps visualizing segregation energy as a function of bulk composition and temperature. (See US-2)
- **FR-007**: System MUST document all data sources with their specific DOIs or URLs in a `data_manifest.json` file. This file MUST contain a list of objects with keys: `source_type`, `source_id`, `doi`, and `url` for every data point used. (See US-1)

### Key Entities

- **SegregationProfile**: Represents the computed equilibrium concentration at the grain boundary for a specific solute, temperature, and bulk composition. Key attributes: `solute_element`, `temperature_K`, `bulk_concentration`, `segregation_energy_eV`, `equilibrium_concentration`.
- **AlloySystem**: Represents a specific chemical system (e.g., Fe-Cr-Mo). Key attributes: `base_element`, `solute_elements`, `calphad_database_id`, `temperature_range`.
- **RegressionModel**: Represents the fitted empirical function. Key attributes: `coefficients`, `interaction_terms`, `r_squared`, `p_values`, `cross_validation_score`, `held_out_mse_reduction`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of statistically significant interaction terms (p<0.05 AND |interaction coefficient| > 0.01 eV) in the multicomponent regression model is measured against the null hypothesis of no cooperative effects. (See US-2)
- **SC-002**: The standard deviation of the R-squared metric across the 5 cross-validation folds must be ≤ 0.05 to confirm model generalizability. (See US-3)
- **SC-003**: The deviation of the computed segregation energy from experimental literature values (e.g., APT measurements) is measured against the experimental baseline to validate the DFT workflow. (See US-1)
- **SC-004**: The percentage of alloy systems where non-linear thresholds for cooperative effects are identified is measured against the total number of systems analyzed. A system is counted only if it satisfies BOTH: (1) |interaction coefficient| > 0.01 eV AND p < 0.05, AND (2) >10% MSE reduction on the held-out test set compared to the additive model. (See US-2)

## Assumptions

- The open CALPHAD thermodynamic database files (e.g., TCFE) contain all necessary interaction parameters for the Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, and Fe-Mo-W systems within the 500-900K temperature range; if parameters are missing for a specific temperature, linear interpolation or extrapolation will be used with a warning.
- The pre-built BCC grain boundary supercell models generated via `pymatgen` from the Materials Project bulk lattice are geometrically stable and suitable for DFT calculations without requiring additional relaxation that would exceed the available compute budget.
- The Quantum ESPRESSO installation on the CI runner is configured with default precision and CPU-only execution; no GPU acceleration or 8-bit quantization is used, ensuring compatibility with the free-tier hardware constraints.
- The McLean isotherm model is a valid approximation for the grain boundary segregation behavior in these BCC systems, and deviations from this model are due to cooperative effects rather than model failure.
- The "free CPU-only CI" environment provides sufficient RAM (≥7 GB) to hold the DFT wavefunction data and regression matrices for the specified alloy systems without requiring disk swapping.
- The dataset variables (bulk concentration, segregation energy, temperature) are sufficient to address the research question; however, **experimental literature data (e.g., APT measurements) is required for the validation step defined in SC-003**.