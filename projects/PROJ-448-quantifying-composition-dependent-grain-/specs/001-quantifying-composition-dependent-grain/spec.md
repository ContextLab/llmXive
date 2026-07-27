# Feature Specification: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Feature Branch**: `001-quantifying-grain-boundary-segregation`  
**Created**: 2026-06-13  
**Status**: Draft  
**Input**: User description: "Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1)

As a materials researcher, I want to compute equilibrium segregation energies and concentrations for specific BCC alloy systems (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V) at defined temperatures using DFT-derived data and the McLean isotherm model, so that I can establish the baseline thermodynamic relationship between bulk composition and grain boundary chemistry.

**Why this priority**: This is the core scientific engine of the project. Without accurate segregation profiles derived from first principles and validated thermodynamic models, no further analysis of non-linearities or cooperative effects is possible. It delivers the primary dataset required for the research question.

**Independent Test**: Can be fully tested by running the computation pipeline on a single binary system (e.g., Fe-Cr) at a single temperature (e.g., 700K) and verifying that the output segregation energy and concentration match the expected values derived from the McLean equation using provided DFT inputs, without requiring the full multicomponent or cross-validation workflow.

**Acceptance Scenarios**:

1. **Given** a valid CALPHAD database file and a pre-built BCC grain boundary supercell model for Fe-Cr, **When** the system executes the DFT energy extraction and McLean isotherm calculation at 700K, **Then** the output file contains a segregation energy value and equilibrium concentration with units of eV and atomic fraction respectively.
2. **Given** a bulk concentration of 0.05 for Cr, **When** the system computes the segregation profile, **Then** the resulting equilibrium concentration at the grain boundary is higher than the bulk concentration (positive segregation) if the segregation energy is negative, consistent with thermodynamic theory.
3. **Given** an invalid or missing supercell model file, **When** the system attempts the calculation, **Then** the process terminates with a clear error message identifying the missing dependency and does not produce a partial or corrupted output file.

---

### User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

As a materials researcher, I want to analyze the computed segregation profiles across ternary alloy systems to identify non-linear thresholds and cooperative effects where the presence of multiple solutes amplifies segregation beyond single-element predictions, so that I can determine if current linear models are insufficient for alloy design.

**Why this priority**: This addresses the specific research gap regarding "cooperative effects" mentioned in the motivation. It moves beyond simple binary analysis to the complex multicomponent behavior that is critical for modern alloy design, providing the "publishable evidence" of non-linearity.

**Independent Test**: Can be fully tested by running the analysis on the pre-computed ternary dataset (Fe-Cr-Mo, etc.) and verifying that the regression model with interaction terms identifies at least one statistically significant interaction coefficient (p<0.05) or a clear deviation from linear additivity in the generated heatmaps.

**Acceptance Scenarios**:

1. **Given** the computed segregation energies for Fe-Cr-Mo across the 500-900K range, **When** the system fits a regression model including interaction terms, **Then** the output includes a coefficient for the Cr-Mo interaction term and a p-value indicating statistical significance if a cooperative effect exists.
2. **Given** a heatmap visualization of segregation energy vs. bulk composition, **When** the researcher inspects the plot, **Then** distinct regions of high segregation are visible that cannot be explained by the sum of binary contributions alone.
3. **Given** a dataset where all interaction terms are zero, **When** the system runs the analysis, **Then** the output explicitly states that no significant cooperative effects were detected within the statistical power of the current sample.

---

### User Story 3 - Model Generalizability and Cross-Validation (Priority: P3)

As a materials researcher, I want to perform k-fold cross-validation (k=5) on the empirical composition-segregation functions across different alloy systems, so that I can assess the robustness and generalizability of the derived relationships before applying them to new alloy designs.

**Why this priority**: This ensures the scientific validity and reproducibility of the findings. It validates that the observed relationships are not artifacts of a specific dataset but represent general physical principles, which is essential for the "rational alloy design" goal.

**Independent Test**: Can be fully tested by executing the cross-validation routine on the existing dataset and verifying that the reported mean squared error (MSE) or R-squared metric remains stable across the 5 folds, with a standard deviation below a defined threshold (e.g., 0.05).

**Acceptance Scenarios**:

1. **Given** a fitted empirical model for the Fe-Cr-Mo system, **When** the system performs 5-fold cross-validation, **Then** the output includes the performance metric (e.g., R²) for each of the 5 folds and the overall mean and standard deviation.
2. **Given** a model trained on Fe-Cr-Mo data, **When** it is tested on a held-out subset of Fe-Cr-V data (if applicable), **Then** the prediction error is reported to assess transferability between systems.
3. **Given** a scenario where the model overfits (high training accuracy, low validation accuracy), **When** the cross-validation is run, **Then** the system flags the high variance between training and validation scores, suggesting the model is not generalizable.

### Edge Cases

- What happens when the CALPHAD database does not contain a specific ternary interaction parameter required for a temperature in the 500-900K range? (System should extrapolate with a warning or flag the data gap).
- How does the system handle DFT convergence failures for specific grain boundary supercells? (System should retry up to 3 times with modified parameters, then log the failure and exclude the data point from the analysis).
- What occurs if the McLean isotherm calculation results in a concentration > 1.0 (physically impossible)? (System should cap the value at 1.0 and log a "saturation" flag for review).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract equilibrium phase compositions for Fe-Cr-Mo, Fe-Cr-V, and Fe-Mo-V ternary systems at temperatures between 500K and 900K from the provided CALPHAD database files. (See US-1)
- **FR-002**: System MUST compute segregation energies using the Quantum ESPRESSO DFT code on pre-built BCC grain boundary supercell models from the Materials Project. (See US-1)
- **FR-003**: System MUST calculate equilibrium segregation profiles using the McLean isotherm model with temperature-dependent parameters derived from the DFT energies. (See US-1)
- **FR-004**: System MUST fit empirical composition-segregation functions using linear regression with interaction terms to capture multicomponent cooperative effects. (See US-2)
- **FR-005**: System MUST perform 5-fold cross-validation across the alloy systems to assess model generalizability and report performance metrics. (See US-3)
- **FR-006**: System MUST generate heatmaps visualizing segregation energy as a function of bulk composition and temperature. (See US-2)
- **FR-007**: System MUST document all data sources with their specific DOIs or URLs in the final output for reproducibility. (See US-1)

### Key Entities

- **SegregationProfile**: Represents the computed equilibrium concentration at the grain boundary for a specific solute, temperature, and bulk composition. Key attributes: `solute_element`, `temperature_K`, `bulk_concentration`, `segregation_energy_eV`, `equilibrium_concentration`.
- **AlloySystem**: Represents a specific chemical system (e.g., Fe-Cr-Mo). Key attributes: `base_element`, `solute_elements`, `calphad_database_id`, `temperature_range`.
- **RegressionModel**: Represents the fitted empirical function. Key attributes: `coefficients`, `interaction_terms`, `r_squared`, `p_values`, `cross_validation_score`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of statistically significant interaction terms (p<0.05) in the multicomponent regression model is measured against the null hypothesis of no cooperative effects. (See US-2)
- **SC-002**: The standard deviation of the R-squared metric across the 5 cross-validation folds is measured against a stability threshold of 0.05 to confirm model generalizability. (See US-3)
- **SC-003**: The deviation of the computed segregation energy from the theoretical McLean prediction (for binary systems) is measured against the expected zero-difference baseline to validate the DFT workflow. (See US-1)
- **SC-004**: The percentage of alloy systems where non-linear thresholds for cooperative effects are identified is measured against the total number of systems analyzed (3 ternary systems). (See US-2)

## Assumptions

- The open CALPHAD thermodynamic database files (e.g., TCFE9) contain all necessary interaction parameters for the Fe-Cr-Mo, Fe-Cr-V, and Fe-Mo-V systems within the 500-900K temperature range; if parameters are missing for a specific temperature, linear interpolation or extrapolation will be used with a warning.
- The pre-built BCC grain boundary supercell models from the Materials Project are geometrically stable and suitable for DFT calculations without requiring additional relaxation that would exceed the 6-hour compute budget.
- The Quantum ESPRESSO installation on the CI runner is configured with default precision and CPU-only execution; no GPU acceleration or 8-bit quantization is used, ensuring compatibility with the free-tier hardware constraints.
- The McLean isotherm model is a valid approximation for the grain boundary segregation behavior in these BCC systems, and deviations from this model are due to cooperative effects rather than model failure.
- The "free CPU-only CI" environment provides sufficient RAM (≥7 GB) to hold the DFT wavefunction data and regression matrices for the specified alloy systems without requiring disk swapping.
- The dataset variables (bulk concentration, segregation energy, temperature) are sufficient to address the research question; no additional experimental data (e.g., atom probe tomography) is required for the computational study itself, though such data would be needed for experimental validation.
