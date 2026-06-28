# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

**Feature Branch**: `001-gut-microbiome-cognitive`  
**Created**: 2025-01-10  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Download and Preprocessing Pipeline (Priority: P1)

The research system must download UK Biobank microbiome 16S rRNA sequencing data and cognitive assessment scores, filter the cohort to participants with both data types, and preprocess microbiome data using quality filtering and centered log-ratio (CLR) transformation.

**Why this priority**: This is the foundational step that enables all downstream analysis. Without clean, properly transformed data, no statistical associations can be computed. This story delivers the minimum viable dataset required for any analysis.

**Independent Test**: Can be fully tested by running the download and preprocessing pipeline on a subset of UK Biobank participants and verifying that the output contains CLR-transformed genus-level abundances and matched cognitive scores for all retained participants.

**Acceptance Scenarios**:

1. **Given** UK Biobank access credentials are valid, **When** the download script executes, **Then** microbiome 16S rRNA sequencing data and cognitive assessment scores (field IDs 20400, 20002) are retrieved for all eligible participants
2. **Given** the raw microbiome reads are available, **When** quality filtering and genus-level aggregation executes, **Then** CLR-transformed taxonomic abundance matrices are produced with no participants missing either microbiome or cognitive data
3. **Given** antibiotic use self-reports are available, **When** the cohort filter executes, **Then** participants with recent antibiotic use are excluded and the exclusion count is logged

---

### User Story 2 - Statistical Association Analysis with Confounder Control (Priority: P2)

The research system must fit linear models testing associations between CLR-transformed taxonomic abundances and cognitive performance scores while controlling for age, sex, BMI, diet quality, physical activity, and medication use, with Benjamini-Hochberg correction for multiple testing.

**Why this priority**: This story delivers the core scientific analysis that answers the research question. It builds on the preprocessing pipeline and produces the primary results (effect sizes, p-values) that determine whether the study has publishable findings.

**Independent Test**: Can be fully tested by running the analysis pipeline on a held-out validation subset and verifying that association statistics (coefficients, p-values, adjusted p-values) are computed for each taxon-cognitive metric pair with appropriate confounder adjustment.

**Acceptance Scenarios**:

1. **Given** the preprocessed CLR-transformed microbiome data and cognitive scores are available, **When** the linear model fitting executes, **Then** association statistics are computed for each genus-level taxon against each cognitive metric (reaction time, numeric memory, reasoning)
2. **Given** multiple hypothesis tests are performed across taxa, **When** multiple comparison correction executes, **Then** Benjamini-Hochberg adjusted p-values are computed and reported for all taxon-cognitive associations
3. **Given** confounder variables are available, **When** the multivariate regression executes, **Then** age, sex, BMI, diet quality, physical activity, and medication use are included as covariates in all models

---

### User Story 3 - Stratified Validation and Visualization (Priority: P3)

The research system must validate findings via stratified analysis by age group (50-65 vs 65+) and generate Manhattan-style plots showing -log10(p-values) for each taxon-cognitive association with effect size annotations.

**Why this priority**: This story delivers the interpretive layer that confirms whether identified associations are age-dependent and provides visual outputs for communication. It depends on the statistical analysis results and enhances the scientific value of the findings.

**Independent Test**: Can be fully tested by running the stratification and visualization pipeline on the analysis results and verifying that separate association statistics are computed for each age group and that Manhattan-style plots are generated with correct p-value transformations.

**Acceptance Scenarios**:

1. **Given** the primary association results are available, **When** stratified analysis executes, **Then** separate linear models are fit for age groups 50-65 and 65+ with effect sizes compared across strata
2. **Given** the association statistics are computed, **When** visualization generation executes, **Then** Manhattan-style plots are produced showing -log10(p-values) for each taxon-cognitive association with effect size annotations
3. **Given** any threshold-based filtering is applied to results, **When** sensitivity analysis executes, **Then** the analysis sweeps the threshold over a small concrete set (e.g., p-value cutoffs ∈ {0.01, 0.05, 0.1}) and reports how the headline rates vary across it

---

### Edge Cases

- What happens when a participant has microbiome data but missing cognitive scores (or vice versa)? The system excludes the participant and logs the count.
- How does the system handle taxa with zero counts in the CLR transformation? The system applies a pseudocount of 1×10⁻⁶ before transformation to avoid log(0).
- What happens when the UK Biobank data download exceeds available disk space (~14 GB)? The system streams data in batches and removes intermediate files after processing.
- How does the system handle participants with incomplete confounder data? The system excludes participants with >2 missing confounder values and logs the exclusion count.
- What happens when the Benjamini-Hochberg correction produces no significant associations? The system reports the maximum adjusted p-value and effect size range rather than failing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download UK Biobank microbiome ribosomal RNA sequencing data and cognitive assessment scores (field IDs 20400, 20002) for all eligible participants (See US-1)
- **FR-002**: System MUST filter the cohort to exclude participants with recent antibiotic use (self-reported medication field) and participants missing either microbiome or cognitive data (See US-1)
- **FR-003**: System MUST apply quality filtering to raw microbiome reads and aggregate to genus-level taxonomy before CLR transformation (See US-1)
- **FR-004**: System MUST fit linear models testing associations between CLR-transformed taxonomic abundances and cognitive performance scores with age, sex, BMI, diet quality, physical activity, and medication use as covariates (See US-2)
- **FR-005**: System MUST apply Benjamini-Hochberg correction for multiple testing across all taxon-cognitive associations and report adjusted p-values (See US-2)
- **FR-006**: System MUST perform stratified analysis by age group (50-65 vs 65+) to assess age-dependent effects (See US-3)
- **FR-007**: System MUST generate Manhattan-style plots showing -log10(p-values) for each taxon-cognitive association with effect size annotations (See US-3)
- **FR-008**: System MUST frame all findings as associational rather than causal given the observational study design (See US-2)
- **FR-009**: System MUST perform collinearity diagnostics on predictor taxa to avoid claiming independent predictive effects for definitionally related taxa (See US-2)
- **FR-010**: System MUST use validated cognitive instruments from the UK Biobank cognitive test batteries (reaction time, numeric memory, reasoning tasks) with citable validation (See US-2)

### Key Entities

- **Participant**: UK Biobank cohort member with linked microbiome and cognitive data, key attributes include participant ID, age, sex, BMI, diet quality score, physical activity level, medication use history, antibiotic use flag
- **MicrobiomeProfile**: CLR-transformed genus-level taxonomic abundance matrix for a participant, key attributes include genus abundances (sum to 1 after transformation), sample collection date, sequencing quality metrics
- **CognitiveScore**: Standardized cognitive performance metric for a participant, key attributes include reaction time (ms), numeric memory score (0-100), reasoning score (0-100), test date
- **AssociationResult**: Statistical output from taxon-cognitive analysis, key attributes include taxon name, cognitive metric, effect size (beta coefficient), unadjusted p-value, Benjamini-Hochberg adjusted p-value, age group stratum

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Cohort retention rate (participants with both microbiome and cognitive data) is measured against the initial UK Biobank sample size after applying antibiotic use and data completeness filters (See US-1)
- **SC-002**: Multiple-comparison error rate is measured against the Benjamini-Hochberg family-wise error correction target (See US-2)
- **SC-003**: Statistical power for detecting effect sizes r > 0.1 is measured against the sample size achieved after filtering, with power calculation deferred to implementation phase (See US-2)
- **SC-004**: Age-stratified effect size consistency is measured against the primary analysis results to assess age-dependent associations (See US-3)
- **SC-005**: Sensitivity analysis outcome variation is measured against the swept threshold set (p-value cutoffs ∈ {0.01, 0.05, 0.1}) to report how headline association rates vary across thresholds (See US-3)
- **SC-006**: Collinearity diagnostic results (variance inflation factors) are measured against the threshold VIF > 5 to flag taxa pairs requiring descriptive framing rather than independent effect claims (See US-2)

## Assumptions

- UK Biobank contains all required variables for the analysis (age, sex, BMI, diet quality scores, physical activity levels, medication use, 16S rRNA sequencing data, cognitive assessment scores) — if any variable is missing, the analysis will be scoped to available confounders and documented
- The study is observational with no random assignment, so all findings will be framed as associational rather than causal relationships
- The analysis will run on a CPU-only GitHub Actions free-tier runner with 2 CPU cores, ~7 GB RAM, ~14 GB disk, and ≤6 h per job
- Microbiome data will be sampled or subset if necessary to fit within 7 GB RAM constraints
- Effect sizes of r > 0.1 will constitute publishable evidence given the cohort size, per the idea's stated threshold
- The Benjamini-Hochberg procedure will control the false discovery rate at α = 0.05 for multiple testing correction
- The sensitivity analysis threshold sweep will use p-value cutoffs ∈ {0.01, 0.05, 0.1} as a concrete, CPU-trivial set
- UK Biobank cognitive instruments (reaction time, numeric memory, reasoning) have been validated in prior work and will be used as-is without additional validation steps
- Taxa with zero counts will be handled with a pseudocount of 1×10⁻⁶ before CLR transformation to avoid log(0)
- Any threshold introduced (e.g., significance cutoff, effect size filter) will carry both a one-line justification naming its community-standard basis and a sensitivity analysis requirement
- The analysis will not require GPU/CUDA accelerators, 8-bit/4-bit quantization, or large-model training — only classical statistics and scikit-learn on CPU are used
- If predictor taxa are definitionally related (e.g., one bounded by another), the analysis will frame their joint relationship descriptively and require collinearity diagnostics rather than claiming independent predictive effects
