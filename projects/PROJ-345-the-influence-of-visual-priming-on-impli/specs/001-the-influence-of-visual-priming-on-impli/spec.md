# Feature Specification: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Feature Branch**: `001-visual-priming-implicit-attitudes`  
**Created**: 2024-05-24  
**Status**: Draft  
**Input**: User description: "The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Stimulus Metadata Extraction (Priority: P1)

The researcher MUST be able to download publicly available IAT response-time datasets and extract corresponding facial stimulus metadata to prepare the data for analysis.

**Why this priority**: This is the foundational step; without valid data ingestion and metadata linkage, no analysis can occur. It delivers the raw material for the research pipeline.

**Independent Test**: Can be fully tested by running the data ingestion script against a known public OSF repository and verifying the output CSV contains trial IDs, response times, and linked stimulus image paths.

**Acceptance Scenarios**:

1. **Given** a public OSF IAT dataset URL, **When** the ingestion script executes, **Then** it outputs a consolidated CSV with response times and stimulus IDs within 60 seconds.
2. **Given** a trial ID with missing linkage metadata in the source dataset, **When** the system queries the metadata store, **Then** it initiates a synthetic linkage derivation process to map the trial to a stimulus image; if *no* data is available for derivation ([deferred] linkage), the system halts and reports 'Data Gap: No linkage data available' before proceeding.
3. **Given** missing image files for >10% of trials, **When** the system processes the dataset, **Then** it halts analysis and reports 'Data Gap: Image files missing for >10% of trials' before proceeding.
4. **Given** missing image files for ≤10% of trials, **When** the system processes the dataset, **Then** it logs a warning and excludes only those specific trials from the analysis subset without crashing.

---

### User Story 2 - Statistical Modeling and Interaction Testing (Priority: P2)

The researcher MUST be able to fit linear mixed-effects models to test for associations between *derived* prime valence and IAT response times, including interaction effects and multiplicity corrections, acknowledging the observational nature of the secondary data analysis.

**Why this priority**: This delivers the core scientific value (hypothesis testing). It builds on the data from US-1 and enables the research conclusions.

**Independent Test**: Can be fully tested by running the modeling script on a sample subset (N=100) and verifying the output model coefficients, p-values, and confidence intervals are generated correctly.

**Acceptance Scenarios**:

1. **Given** preprocessed trial data, **When** the model fits a linear mixed-effects regression, **Then** it reports fixed effects for *derived* prime valence and stimulus ambiguity with p-values calculated at α = 0.05.
2. **Given** multiple hypothesis tests (e.g., interactions across demographic groups), **When** the system computes significance, **Then** it applies False Discovery Rate (FDR) correction to the family-wise error rate.
3. **Given** a model convergence failure, **When** the system retries, **Then** it attempts multiple alternative optimizer settings before flagging the dataset as unsuitable for this model structure.

---

### User Story 3 - Reporting and Visualization Generation (Priority: P3)

The researcher MUST be able to generate publication-ready plots and summary tables that visualize the interaction effects and effect sizes.

**Why this priority**: This delivers the final output for dissemination. It depends on US-2 completing successfully.

**Independent Test**: Can be fully tested by running the reporting script and verifying the existence of a PDF report containing interaction plots and a coefficient table.

**Acceptance Scenarios**:

1. **Given** a fitted model object, **When** the reporting script executes, **Then** it generates an interaction plot showing response time differences across prime valence conditions.
2. **Given** significant interaction effects, **When** the system computes effect sizes, **Then** it calculates Cohen's d and partial eta-squared with confidence intervals via bootstrapping (a sufficient number of resamples).
3. **Given** the alpha sensitivity analysis, **When** the system compares thresholds, **Then** it reports how the significance rate varies across standard significance thresholds.

---

### Edge Cases

- **Missing Stimulus Images**: If the dataset claims to include images but files are missing for >10% of trials, the system MUST halt analysis and report the data gap rather than proceeding with incomplete data. If files are missing for ≤10% of trials, the system MUST exclude only those trials and proceed.
- **Model Convergence Failure**: If the linear mixed-effects model fails to converge after multiple optimizer attempts, the system MUST log the failure and suggest simplifying the random effects structure.
- **High Collinearity**: If predictors (e.g., *derived* prime valence and stimulus ambiguity) show VIF > 5.0, the system MUST flag this in the output and refrain from claiming independent predictive effects.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST verify the presence of trial-level response times, prime valence labels, and stimulus ambiguity scores before analysis begins; if ambiguity scores are missing, the system MUST derive them via an annotation pipeline or synthetic generation (See US-1).
- **FR-002**: System MUST derive valence scores from stimulus images using CPU-optimized emotion classification models if the stimulus is an image, or use a lexical valence dictionary if the stimulus is a word (See US-1).
- **FR-003**: System MUST frame all statistical findings as associational rather than causal, given the observational nature of the secondary data analysis and the use of *derived* prime valence (See US-2).
- **FR-004**: System MUST apply multiple-comparison correction (e.g., FDR or Bonferroni) when testing >1 hypothesis to control family-wise error rate (See US-2).
- **FR-005**: System MUST compute Variance Inflation Factor (VIF) for predictors and flag values > 5.0 to detect collinearity (See US-2).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the significance threshold across a range of standard α levels to assess robustness of results (See US-2).

### Key Entities

- **Trial**: A single response event containing response time, stimulus ID, and prime condition.
- **Participant**: A unique identifier for the subject providing multiple trials.
- **Stimulus**: An image file or word string with metadata regarding facial expression valence and ambiguity scores (derived if not present).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data ingestion completeness is measured against the design target that The vast majority of trials have linked stimulus metadata. (See US-1).
- **SC-002**: Model convergence success rate is measured against the design target that ≥[configurable: [deferred]] of fitted models converge within 3 optimizer attempts (See US-2).
- **SC-003**: Report artifact completeness is measured against the requirement that the final PDF contains interaction plots, coefficient tables, and sensitivity analysis summaries (See US-3).

## Assumptions

- Public IAT datasets are accessible via direct HTTP GET without OAuth or institutional login.
- The CI environment provides ≥7 GB RAM and 2 CPU cores to support linear mixed-effects modeling on CPU.
- Source IAT data includes trial-level timestamps and stimulus IDs sufficient for priming simulation.
- Pre-trained emotion classifiers used for valence scoring are available as CPU-optimized Python packages (e.g., via `torch` CPU backend).
- Demographic covariates (e.g., age, gender) are available in the participant metadata for random effects modeling.
- **Hardware Constraint**: The system is assumed to run in a CPU-only environment; GPU acceleration is not required.