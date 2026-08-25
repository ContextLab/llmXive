# Feature Specification: Mindfulness Components and Delivery Formats in ASD Social Skills

## User Stories

### US1: Data Collection and Cleaning Pipeline (P1)
**As a** researcher,
**I want** to collect study data from ClinicalTrials.gov and OSF,
**so that** I can extract standardized variables for meta-analysis.

**Acceptance Criteria**:
- [ ] Studies are retrieved from ClinicalTrials.gov and OSF only (Constitution Principle VI)
- [ ] Inclusion criteria: age 6-12, ASD diagnosis, social skill outcomes
- [ ] Multi-arm studies are handled by splitting control groups proportionally
- [ ] Output: `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log`

### US2: Effect Size Calculation and Meta-Analysis (P2)
**As a** researcher,
**I want** to calculate Hedges' g effect sizes and perform random-effects meta-analysis,
**so that** I can quantify intervention efficacy and heterogeneity.

**Acceptance Criteria**:
- [ ] Hedges' g calculated with small-sample correction
- [ ] Random-effects model used if I² > 50%
- [ ] Subgroup analysis for mindfulness components and delivery formats
- [ ] Follow-up duration analysis (3-month vs. others)
- [ ] If N < 10, switch to descriptive synthesis (no meta-regression)

### US3: Visualization and Publication Bias Assessment (P3)
**As a** researcher,
**I want** to generate forest plots and funnel plots,
**so that** I can visualize results and assess publication bias.

**Acceptance Criteria**:
- [ ] Forest plot shows study-specific CIs and pooled effect diamond
- [ ] Funnel plot generated only if N ≥ 10
- [ ] Egger's test for publication bias (only if N ≥ 10)
- [ ] Final report includes all plots and narrative synthesis

## Functional Requirements

- **FR-001**: Data collector must support ClinicalTrials.gov and OSF APIs
- **FR-002**: Rate-limiting and exponential backoff for API calls
- **FR-003**: Extract intervention components using regex patterns
- **FR-004**: Calculate Hedges' g with small-sample correction
- **FR-005**: Random-effects meta-analysis with heterogeneity statistics
- **FR-006**: Generate forest and funnel plots (matplotlib)
- **FR-007**: Validate data against schema contracts
- **FR-008**: Handle multi-arm studies by proportional control splitting
- **FR-009**: Abstract-only text extraction fallback (no full-text OCR)
- **FR-010**: Extract social skill domains (communication, peer interaction, etc.)
- **FR-011**: Subgroup analysis by social skill domain
- **FR-012**: Follow-up duration subgroup analysis
- **FR-013**: Effect size calculation from summary statistics
- **FR-014**: Conditional logic: suppress meta-regression if N < 10

## Non-Functional Requirements

- **SC-005**: Reproducibility on fresh runner (CI/CD pipeline)
- **CPU Constraint**: No GPU dependencies
- **Memory Limit**: ≤ 7GB RAM, ≤ 14GB disk
- **Data Integrity**: All artifacts hashed (Constitution Principle V)
- **Ethics**: Secondary analysis exempt from IRB (T009)

## Data Models

- **Study**: id, title, registry, population, intervention, control, outcomes, follow_up
- **EffectSize**: study_id, hedges_g, se, ci_lower, ci_upper, n_treatment, n_control
- **MetaAnalysisResult**: pooled_g, se, ci, i2, q_statistic, p_value, n_studies

## Schema Contracts

- `contracts/cleaned_study.schema.yaml`
- `contracts/effect_size.schema.yaml`
