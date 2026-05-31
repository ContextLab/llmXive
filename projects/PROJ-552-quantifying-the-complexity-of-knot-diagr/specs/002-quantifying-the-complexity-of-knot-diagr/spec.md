# Feature Specification: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `[001-quantifying-knot-complexity]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "How does the relationship between crossing number and braid index vary across different classes of prime knots, and what structural properties of knot diagrams are jointly determined by these invariants?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Parse Knot Dataset (Priority: P1)

As a researcher, I want to download and parse knot data from the Knot Atlas including crossing numbers, braid indices, and prime knot classifications for all knots with crossing number ≤13, so that I have a consistent, clean dataset for analysis.

**Why this priority**: This is the foundational step—without reliable data, no analysis can proceed. The methodology sketch explicitly requires this as the first step.

**Independent Test**: Can be fully tested by verifying the dataset downloads successfully, parses correctly, and contains the required fields (crossing number, braid index, prime knot classification) for all knots up to crossing number 13.

**Acceptance Scenarios**:

1. **Given** a valid connection to Knot Atlas, **When** the system downloads knot data, **Then** the dataset includes crossing numbers, braid indices, and prime knot classifications for all knots with crossing number ≤13
2. **Given** the downloaded data contains inconsistent representations, **When** the parsing and cleaning process runs, **Then** the output dataset has consistent, normalized representations of crossing number and braid index for each prime knot

---

### User Story 2 - Compute Additional Invariants and Perform Exploratory Analysis (Priority: P2)

As a researcher, I want to compute additional invariants (arc index, Seifert circle count, bridge number) and perform exploratory data analysis including scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification, so that I can understand the correlation structure between these invariants.

**Why this priority**: This represents the core research activity—understanding the relationship between the two primary invariants and how it varies across knot classes.

**Independent Test**: Can be fully tested by generating scatter plots showing crossing number vs. braid index, stratified by alternating/non-alternating classification, and verifying that additional invariants are computed for each knot in the dataset.

**Acceptance Scenarios**:

1. **Given** a clean dataset of prime knots, **When** the system computes additional invariants, **Then** arc index, Seifert circle count, and bridge number are available for each knot where diagram representations are available
2. **Given** the complete dataset with computed invariants, **When** exploratory analysis runs, **Then** scatter plots of crossing number vs. braid index are generated, stratified by alternating/non-alternating classification

---

### User Story 3 - Fit Models and Construct Composite Complexity Measure (Priority: P3)

As a researcher, I want to fit multiple regression models to test linear vs. non-linear relationships and construct a composite complexity score as a weighted combination of crossing number and braid index, so that I can validate whether the composite measure shows predictive power for related structural properties.

**Why this priority**: This is the advanced analysis that tests the expected results hypothesis about non-linear correlation and composite measures. It depends on P1 and P2 being complete.

**Independent Test**: Can be fully tested by validating the composite measure against held-out knots and testing correlation with arc index and Seifert circle count.

**Acceptance Scenarios**:

1. **Given** the exploratory analysis results, **When** multiple regression models are fitted, **Then** the system identifies whether linear or non-linear relationships better describe the crossing number vs. braid index relationship
2. **Given** a constructed composite complexity score, **When** validated against held-out knots, **Then** the composite measure shows correlation with arc index and Seifert circle count that neither invariant alone captures with comparable accuracy

---

### Edge Cases

- What happens when Knot Atlas data is unavailable or the download fails?
- How does the system handle knots where braid index or other invariants are not documented in the source data?
- How does the system handle knots with crossing number >13 that appear in the dataset?
- What happens when the regression models fail to converge or produce statistically insignificant results?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download knot data from Knot Atlas (https://katlas.org) including crossing numbers, braid indices, and prime knot classifications for all knots with crossing number ≤13
- **FR-002**: System MUST parse and clean the dataset to extract consistent representations of crossing number and braid index for each prime knot
- **FR-003**: System MUST compute additional invariants (arc index, Seifert circle count, bridge number) from available diagram representations
- **FR-004**: System MUST perform exploratory data analysis including scatter plots of crossing number vs. braid index, stratified by alternating/non-alternating classification
- **FR-005**: System MUST fit multiple regression models to test linear vs. non-linear relationships between crossing number and braid index
- **FR-006**: System MUST construct a composite complexity score as a weighted combination of crossing number and braid index
- **FR-007**: System MUST validate the composite measure against held-out knots by testing correlation with arc index and Seifert circle count
- **FR-008**: System MUST apply statistical tests (Pearson/Spearman correlation, ANOVA for group differences) to assess significance of findings
- **FR-009**: System MUST document all code and data transformations for reproducibility
- **FR-010**: System MUST apply statistical tests including Pearson/Spearman correlation and ANOVA for group differences to assess significance of findings

### Key Entities

- **Knot**: A prime knot with attributes including crossing number, braid index, alternating classification, arc index, Seifert circle count, and bridge number
- **Composite Complexity Score**: A derived metric combining crossing number and braid index with configurable weights for validation against other structural properties

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dataset contains at least 9,988 (https://doi.org/10.1142/s0218216525500099, https://doi.org/10.1142/s0218216525500099)prime knots with crossing number ≤13 (as referenced in the 2024 minimal grid diagrams study)
- **SC-002**: Statistical significance of correlation findings is established with p < 0.05 for Pearson/Spearman correlation tests
- **SC-003**: Composite complexity measure shows higher correlation coefficient with arc index and Seifert circle count than either crossing number or braid index alone
- **SC-004**: All code and data transformations are documented with sufficient detail for independent reproducibility
- **SC-005**: Regression model comparison identifies whether linear or non-linear relationship better describes the data (at least one model achieves R² > 0.5)

## Assumptions

- Knot Atlas (https://katlas.org) provides accessible, structured data for all prime knots with crossing number ≤13
- The 2024 minimal grid diagrams dataset (9,988 prime knots) is available as a testable dataset for correlation analysis as referenced in the methodology
- Sufficient computational resources exist to download, parse, and analyze the complete dataset
- Statistical analysis libraries are available for implementing Pearson/Spearman correlation and ANOVA tests
- The distinction between alternating and non-alternating prime knots is determinable from the source data
- [NEEDS CLARIFICATION: What specific weight combination methodology should be used for the composite complexity score?]
- [NEEDS CLARIFICATION: What proportion of the dataset should be held out for validation of the composite measure?]
- [NEEDS CLARIFICATION: Should the analysis include virtual knots in addition to classical prime knots based on the 2022 generalized knots reference?]
