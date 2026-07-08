# Feature Specification: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

**Feature Branch**: `001-multi-property-trade-offs`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Extraction and Composition Encoding (Priority: P1)

**Journey**: A materials researcher needs to ingest a subset of public alloy data (e.g., OQMD or Materials Project), filter for entries containing paired mechanical properties (yield strength and elongation), and encode these compositions into a feature vector using elemental fractions and periodic table descriptors (atomic radius, electronegativity).

**Why this priority**: Without a clean, encoded dataset containing both the composition and the target properties, no modeling or trade-off analysis can occur. This is the foundational data pipeline required for any subsequent step.

**Independent Test**: Can be fully tested by running the data ingestion script against a known small subset of the public API and verifying the output CSV contains non-null values for composition, strength, and ductility, with feature vectors of the correct dimension.

**Acceptance Scenarios**:

1. **Given** a public dataset endpoint is accessible, **When** the script filters for Fe-Cr or Al-Cu systems and encodes entries with both yield strength and elongation > 0, **Then** the output dataset contains valid feature vectors for all successfully processed entries, and if the total count is < 500, the system logs a specific warning "Insufficient data for statistical analysis (N < 500)" and exits with code 0.
2. **Given** a dataset entry lacks one of the required properties (strength or ductility), **When** the ingestion script processes it, **Then** the entry is excluded from the training/test split without causing a pipeline crash.
3. **Given** a valid alloy composition, **When** the encoder runs, **Then** the output feature vector includes elemental fractions and at least two periodic descriptors (atomic radius, electronegativity) for each element present.

---

### User Story 2 - Surrogate Model Training and Pareto Frontier Generation (Priority: P2)

**Journey**: A researcher trains separate CPU-based gradient-boosting regressors for strength and ductility on the encoded data, then uses these models to generate synthetic composition points within the convex hull to compute empirical Pareto frontiers via a multi-objective evolutionary algorithm (NSGA-II).

**Why this priority**: This step transforms raw data into predictive models and identifies the theoretical "best" trade-off curves. It is the core analytical engine of the project.

**Independent Test**: Can be fully tested by training the models on a fixed random seed, generating a set of synthetic points, and verifying that the resulting Pareto frontier consists of non-dominated points that improve upon the raw test set distribution.

**Acceptance Scenarios**:

1. **Given** a training set of encoded alloys, **When** the gradient-boosting models are trained on CPU (max 2 cores), **Then** the system calculates and reports the cross-validated R² score for each target property on the held-out test set.
2. **Given** trained models and a convex hull of the training data, **When** the NSGA-II algorithm generates a set of synthetic points, **Then** the resulting Pareto frontier contains the set of non-dominated points found by the algorithm.
3. **Given** the empirical test data and theoretical thermodynamic limits (Rule of Mixtures), **When** the model-derived frontier is overlaid, **Then** the system calculates and outputs the percentage of test points dominated by the model frontier and the percentage of the model frontier that strictly dominates the empirical set.

---

### User Story 3 - Trade-Off Decoupling Analysis and Visualization (Priority: P3)

**Journey**: A researcher identifies specific compositional clusters where strength and ductility are decoupled (low correlation) and visualizes these regions in 2D composition-property space to highlight candidate design zones.

**Why this priority**: This delivers the specific scientific insight requested in the research question—identifying "decoupled" regions—allowing the researcher to make informed design decisions.

**Independent Test**: Can be tested by running the analysis on a fixed dataset and verifying the output includes a 2D plot where regions of low correlation are distinctly marked and the correlation coefficient is reported for those regions.

**Acceptance Scenarios**:

1. **Given** the full dataset and model predictions, **When** the correlation analysis runs using composition-based clustering, **Then** the system identifies the cluster with the minimum correlation between strength and ductility and reports the correlation coefficient.
2. **Given** identified decoupled regions, **When** the visualization module runs, **Then** a 2D plot is generated showing the compositional space with the decoupled region highlighted and the theoretical Pareto frontier overlaid.
3. **Given** the uncertainty metrics (cross-validation variance) and a configurable threshold parameter, **When** the analysis flags unreliable regions, **Then** the visualization excludes or shades regions where the prediction variance exceeds the configured threshold.

---

### Edge Cases

- What happens when the public dataset API returns a limited number of valid entries for a specific alloy system (e.g., a rare ternary system)? The system must fail gracefully with a clear error message indicating insufficient data for statistical analysis.
- How does the system handle compositional points on the boundary of the convex hull where extrapolation might lead to physically impossible property predictions? The system must clamp predictions to known physical limits (e.g., ductility ≤ 100%) and flag these points as "extrapolated."
- What occurs if the NSGA-II algorithm fails to converge within a predefined computational time limit? The system must output the best non-dominated set found so far and log a warning about incomplete convergence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and filter public alloy datasets (OQMD/Materials Project) for entries containing both yield strength and elongation values, excluding any with missing data (See US-1).
- **FR-002**: System MUST encode alloy compositions into feature vectors using elemental fractions and periodic descriptors (atomic radius, electronegativity) for all elements present (See US-1).
- **FR-003**: System MUST train separate gradient-boosting regressors for each target property using scikit-learn on CPU with a maximum of 2 cores and memory usage within available limits (<7GB RAM) (See US-2).
- **FR-004**: System MUST generate synthetic composition points within the convex hull of the training data and compute Pareto frontiers using a multi-objective evolutionary algorithm (See US-2).
- **FR-005**: System MUST identify compositional clusters using a composition-based method (e.g., K-Means on elemental fractions) and calculate the correlation between competing properties for each cluster to identify the region with the lowest correlation (See US-3).
- **FR-006**: System MUST calculate and report prediction uncertainty (cross-validation variance) for all generated points, flagging regions where variance exceeds a configurable threshold parameter (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on the decoupling threshold (correlation cutoff) by sweeping a configurable set of values and reporting the change in identified region size (See US-3).
- **FR-008**: System MUST validate model generalizability using Leave-One-System-Out Cross-Validation (LOSO-CV) to ensure the Pareto frontier is not an interpolation artifact of the training data (See US-2).

### Key Entities

- **AlloyEntry**: Represents a single data point from the public dataset, containing composition (elements, fractions), yield strength, elongation, and encoded feature vector.
- **ParetoFrontier**: A set of non-dominated synthetic composition points representing the optimal trade-off curve between two properties.
- **DecoupledRegion**: A defined cluster in composition space (identified via composition-based clustering) where the correlation between two properties falls below a specified threshold.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of test set points dominated by the model-derived Pareto frontier and the percentage of the frontier strictly dominating the empirical set are measured against the theoretical thermodynamic limits (Rule of Mixtures) to assess model fidelity (See US-2).
- **SC-002**: The correlation coefficient between strength and ductility in the identified "decoupled" region (minimum correlation cluster) is measured against the global correlation coefficient of the entire dataset to quantify decoupling (See US-3).
- **SC-003**: The size (number of points) of the identified decoupled regions is measured against the sensitivity analysis sweep results (configurable correlation cutoffs) to validate threshold robustness (See US-3).
- **SC-004**: The R² score of the surrogate models on the held-out test set (via LOSO-CV) is measured against the baseline of a null model (predicting the mean) to ensure predictive utility (See US-2).
- **SC-005**: The variance of predictions in flagged "unreliable" regions is measured against the global prediction variance to confirm the uncertainty metric is functioning (See US-3).

## Assumptions

- The public datasets (OQMD or Materials Project) contain sufficient entries with both yield strength and elongation values for the selected alloy systems (e.g., Fe-Cr, Al-Cu) to support statistical modeling (target ≥ 500 valid entries).
- The computational environment (GitHub Actions free-tier) provides sufficient CPU resources (multiple cores, Approximately several gigabytes of RAM.) to run gradient-boosting and NSGA-II algorithms within the specified time limit without GPU acceleration.
- The relationship between composition and properties in the public datasets is sufficiently captured by elemental fractions and simple periodic descriptors (atomic radius, electronegativity) without requiring complex crystal structure features.
- The "decoupling" of properties is a real phenomenon in the data and not an artifact of measurement noise or dataset bias.
- The sensitivity analysis for the correlation threshold (sweeping configurable values) is computationally trivial and will not significantly impact the total runtime.
- The NSGA-II algorithm will converge to a stable Pareto frontier within the allocated time budget for the specified problem size.