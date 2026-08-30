# Feature Specification: Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance

**Feature Branch**: `001-soil-microbiome-diversity-disease-resistance`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

Researcher downloads processed 16S rRNA amplicon tables from Earth Microbiome Project (EMP) agricultural subset or MG-RAST soil microbiome repository, obtains plant disease incidence records from published agricultural soil microbiome studies with matched metadata (plant species, GPS coordinates, soil type, disease incidence rate), and retrieves associated metadata from study metadata files. The data is filtered (OTU/ASV tables to retain taxa present in ≥5% of samples), rarefied to uniform sequencing depth, and disease incidence data is aligned with matching soil samples via location and date fields.

**Critical Feasibility Note**: Prior reviews confirm that NO verified open-source dataset exists containing both matched S rRNA amplicon tables and plant disease incidence records. If the system cannot find ≥30 matched samples of **verified real data**, it MUST NOT proceed with hypothesis testing. Instead, it MUST generate a "Feasibility Report" documenting the data gap and halt downstream analysis. **Synthetic data is strictly prohibited for hypothesis testing.**

**Why this priority**: Without clean, aligned data from both sources, no downstream analysis can proceed. This is the foundational data layer that enables all statistical modeling and hypothesis testing.

**Independent Test**: Can be fully tested by verifying that the downloaded dataset contains sufficient samples for downstream analysis, disease records contain disease incidence entries, and the merged dataset has matched samples with complete metadata (plant species, GPS, soil type, disease incidence rate). If no matched real data is found, the system MUST generate a Feasibility Report.

**Acceptance Scenarios**:

1. **Given** MG-RAST and Qiita agricultural soil microbiome data sources are accessible, **When** researcher executes data download scripts, **Then** the system attempts to retrieve ≥100 EMP/MG-RAST samples (or all available if <100) and reports the count. **If** ≥30 matched samples with complete metadata are found, **Then** the system proceeds. **ELSE**, the system MUST log [INSUFFICIENT_SAMPLES] and generate a "Feasibility Report" detailing the data gap. **The system MUST verify the logic of this check: if <30 samples are found, it MUST correctly trigger the Feasibility Report.**
2. **Given** raw OTU/ASV tables contain taxa with <5% prevalence, **When** filtering is applied, **Then** only taxa present in ≥5% of samples are retained and rarefied to a uniform sequencing depth.
3. **Given** a disease dataset download attempt, **When** the system queries available sources, **Then** if no verified source with matched disease incidence is found, the system MUST log [MISSING_DATASET] and halt with a Feasibility Report.
4. **Given** a request to join disparate datasets (e.g., EMP soil data + generic GPS data) via metadata, **Then** the system MUST reject the request and log [INVALID_JOIN] as this approach cannot answer the research question.

---

### User Story 2 - Statistical Analysis and Model Fitting (Priority: P2)

Researcher computes alpha-diversity metrics (Shannon, Simpson, Faith's PD) per sample using QIIME 2's `diversity alpha` plugin, then fits beta regression or binomial generalized linear mixed-effects models (GLMM) with disease incidence as response (proportion data), alpha diversity as fixed effect, and random intercepts for plant species and geographic region. The diversity coefficient significance (p<0.05) and effect size are reported, with permutation tests (10,000 permutations) confirming observed correlations exceed random expectations. Additionally, the researcher performs stratified analysis by crop type subset (as required by robustness section) to assess whether the diversity-disease relationship holds across different agricultural contexts, reporting consistency of effect direction and magnitude across subsets.

**Critical Constraint**: This analysis MUST ONLY be performed on **verified real data**. The use of synthetic or randomly generated disease labels for hypothesis testing is explicitly prohibited as it invalidates the biological hypothesis. If real matched data is unavailable, the system MUST NOT fit the model and MUST report "Insufficient Data to Test Hypothesis". **Code validation (unit tests) may use dummy data, but such runs MUST NOT produce scientific findings.**

**Why this priority**: This is the core research hypothesis test that directly answers the research question. Without valid statistical models on real data, no conclusions about microbiome diversity and disease resistance can be drawn. The crop subset analysis addresses the robustness requirement from the original idea.

**Independent Test**: Can be fully tested by running the statistical analysis pipeline on a subset of 30 matched samples and verifying that a beta regression or binomial GLMM produces a p-value for the diversity coefficient, that permutation test results are reproducible, and that crop subset stratification produces consistent effect directions. If real data is unavailable, the system MUST report "Insufficient Data".

**Acceptance Scenarios**:

1. **Given** ≥30 matched samples with computed alpha-diversity metrics, **When** beta regression or binomial GLMM is fitted with disease incidence as response, **Then** the system MUST report the diversity coefficient p-value, effect size, and 95% confidence interval (regardless of whether p<0.05).
2. **Given** observed correlation coefficient, **When** 10,000 permutation tests are executed, **Then** the system MUST report the p-permutation value and compare it against the alpha=0.05 threshold.
3. **Given** samples stratified by crop type into ≥2 subsets, **When** diversity-disease model is fitted per subset, **Then** effect direction (positive/negative) is consistent across ≥80% of subsets with effect sizes within same order of magnitude. **ELSE**, if <2 subsets with N≥15 exist, the system MUST report "Insufficient data for stratification". **The system MUST verify the implementation of stratification: if N<15 per subset, it MUST correctly report 'Insufficient data' rather than attempting to fit a model.**
4. **Given** a request to run the pipeline on synthetic data for hypothesis testing, **Then** the system MUST reject the request and log [SYNTHETIC_DATA_PROHIBITED].
5. **Given** a unit test run with dummy data, **Then** the system MUST execute the code but MUST NOT output p-values, effect sizes, or any scientific findings.

---

### User Story 3 - Keystone Taxon Identification and Network Analysis (Priority: P3)

Researcher performs differential abundance testing (ANCOM-BC) between high- and low-disease sites to highlight taxa enriched in disease-suppressed soils, then constructs co-occurrence networks (CoNet) and computes node centrality. Taxa with high betweenness/degree are flagged as putative keystones.

**Why this priority**: This provides mechanistic insight beyond the diversity-level correlation, identifying specific taxa that may drive disease suppression. It is secondary to establishing the core diversity-disease relationship.

**Independent Test**: Can be fully tested by running ANCOM-BC on a subset of samples and verifying that ≥3 taxa are identified with differential abundance (q<0.1) and that co-occurrence network produces ≥10 nodes with centrality metrics computed.

**Acceptance Scenarios**:

1. **Given** samples stratified into high/low disease groups, **When** ANCOM-BC is executed, **Then** ≥3 taxa are identified with differential abundance (q<0.1) enriched in disease-suppressed soils.
2. **Given** ≥30 samples with taxonomic composition, **When** CoNet co-occurrence network is constructed, **Then** ≥10 nodes have betweenness/degree centrality computed and ≥2 taxa flagged as putative keystones.

---

### Edge Cases

- What happens when EMP/MG-RAST and disease datasets cannot be matched via location and date fields (fewer than 30 matched samples)? **System MUST generate a Feasibility Report and halt.**
- How does system handle when sequencing depth varies widely (>10x difference) and rarefaction discards >50% of reads? **System MUST log [LOW_RECOVERY_RATE] and report the percentage of reads retained.**
- What happens when beta regression or binomial GLMM fails to converge (singular fit, boundary issues)? **System MUST log [MODEL_CONVERGENCE_FAILURE] and report the error.**
- How does system handle when ANCOM-BC differential abundance testing produces no significant taxa (q≥0.1 for all)? **System MUST report "No significant taxa found" and not flag any keystones.**
- What happens when the system attempts to join disparate datasets (e.g., EMP soil data + generic GPS data)? **System MUST reject the join and log [INVALID_JOIN].**

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST attempt to download 16S rRNA amplicon tables from Earth Microbiome Project agricultural subset or MG-RAST soil microbiome repository. System MUST report the count of samples retrieved. **If** the count is <100, the system MUST proceed with all available samples. **If** <30 matched samples with complete metadata are found, the system MUST log [INSUFFICIENT_SAMPLES] and trigger the fallback path (FR-016). (See US-1)
- **FR-002**: System MUST rarefy OTU/ASV tables to uniform sequencing depth using QIIME 2 and MUST output the artifact `data/processed/rarefied-table.qza`. **This requirement is conditional on the existence of valid input data per FR-001.** (See US-1)
- **FR-003**: System MUST compute alpha-diversity metrics (Shannon, Simpson, Faith's PD) per sample using QIIME 2's `diversity alpha` plugin. (See US-2)
- **FR-004**: System MUST fit beta regression or binomial generalized linear mixed-effects models with disease incidence (proportion 0-100%) as response, alpha diversity as fixed effect, and random intercepts for plant species and geographic region. **CRITICAL**: This MUST ONLY be performed on verified real data. If real matched data is unavailable, the system MUST NOT fit the model and MUST report "Insufficient Data to Test Hypothesis". **Synthetic data is strictly prohibited for hypothesis testing. Unit tests using dummy data MUST NOT produce scientific findings.** (See US-2)
- **FR-005**: System MUST conduct permutation tests with N=10,000 iterations to confirm observed correlations exceed random expectations. **The permutation strategy MUST be restricted (e.g., permuting within clusters) to maintain the null hypothesis validity in mixed-effects models, preventing inflated Type I error rates.** (See US-2)
- **FR-006**: System MUST perform differential abundance testing using ANCOM-BC (the standard, bias-corrected implementation of ANCOM) between high- and low-disease sites to identify taxa enriched in disease-suppressed soils. **The system MUST frame these findings as 'candidate taxa' associated with disease suppression, NOT as 'keystone drivers' or causal agents, to avoid tautological claims.** (See US-3)
- **FR-007**: System MUST construct co-occurrence networks (CoNet) and compute node centrality (betweenness/degree) for keystone taxon identification. (See US-3)
- **FR-008**: System MUST verify that EMP/MG-RAST dataset contains required variables: OTU/ASV tables, plant species, GPS coordinates, soil type, sequencing depth. System MUST verify that disease dataset contains required variables: sample ID, disease type, incidence rate (0-100%), measurement date. **If** the disease dataset download yields 0 records (no source found), the system MUST record [MISSING_DATASET] and halt. **If** partial data is found but variables are missing, record explicit [MISSING_VARIABLE: <variable-name>] marker with count of affected samples. **If** the disease dataset is missing, the system MUST NOT attempt variable verification on non-existent data. (See US-1)
- **FR-009**: System MUST frame all statistical findings as ASSOCIATIONAL (not causal) since no random assignment exists in observational design. (See US-2)
- **FR-010**: System MUST apply multiple-comparison / family-wise-error correction when >1 hypothesis test is run. (See US-2)
- **FR-011**: System MUST perform stratified analysis by crop type subset and report the consistency of effect direction and magnitude across subsets. **The system MUST require a minimum of N≥30 samples per subset for stratified analysis; if N<30 per subset, the system MUST report 'Insufficient data for stratification' to prevent overfitting.** (See US-2)
- **FR-012**: System MUST diagnose predictor collinearity when two predictors are definitionally related and frame joint relationships descriptively. (See US-2)
- **FR-015**: System MUST conduct a priori power analysis (power ≥0.8, alpha=0.05) to determine minimum sample size for detecting diversity effect on disease incidence with effect size ≥0.1 (community standard). The effect size assumption MUST be derived from published meta-analyses or real data variance. **If** real data variance is unavailable, the system MUST use the published assumption and log [INSUFFICIENT_DATA_FOR_POWER] if the assumption cannot be validated. (See US-1, US-2)
- **FR-016**: System MUST handle data unavailability. If matched disease records cannot be found (e.g., <30 matched samples, or no verified source exists), the system MUST halt statistical analysis and generate a "Feasibility Report" documenting the specific data gap (e.g., "No verified source found for matched disease incidence"). **Synthetic data generation for hypothesis testing is strictly prohibited.** (See US-1)
- **FR-017**: System MUST perform propensity score matching or include explicit soil chemistry covariates (pH, organic matter, texture) in the model to decouple host/soil effects from microbial diversity, addressing the confounding variable concern. (See US-2)
- **FR-018**: System MUST conduct a sensitivity analysis sweeping a range of small to moderate effect size assumptions to validate the power analysis robustness., addressing the heterogeneity concern. (See US-2)

### Key Entities

- **Sample**: Represents a single soil microbiome collection with attributes: sample ID, GPS coordinates, plant species, soil type, sequencing depth, alpha-diversity metrics
- **Disease Incidence**: Represents plant disease measurement with attributes: sample ID (optional, may be null if dataset is incomplete), disease type, incidence rate (0-100%), measurement date
- **Taxon**: Represents microbial taxonomic unit with attributes: taxon ID, taxonomic lineage, relative abundance, differential abundance q-value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation coefficient between alpha-diversity (Shannon/Simpson) and disease incidence is measured against published meta-analysis values from soil microbiome-disease literature (See US-2)
- **SC-002**: Model fit statistics (R², AIC) for beta regression/GLMM are measured against null model baseline (See US-2)
- **SC-003**: Number of keystone taxa identified with differential abundance (q<0.1) is measured against ANCOM-BC output (See US-3)
- **SC-004**: Permutation test p-value stability is measured across multiple independent runs with N=10,000 permutations (See US-2)
- **SC-005**: Multiple-comparison correction applied rate is measured against total hypothesis tests run (≥100% correction coverage required) (See US-2)
- **SC-006**: Data acquisition quality is measured as the percentage of required variables found in available datasets. **System MUST verify the existence of the disease dataset; if missing, record [MISSING_DATASET] and report [deferred] completeness. If present, measure completeness against required variables.** (See US-1)

## Assumptions

- EMP agricultural subset and MG-RAST soil microbiome data sources remain accessible and unchanged during the analysis window
- **Critical Reality**: NO verified open-source dataset exists for matched 16S rRNA and disease incidence records. The system MUST handle this by generating a Feasibility Report (FR-016) if the data gap is confirmed. **Synthetic data is strictly prohibited for hypothesis testing.**
- Beta regression or binomial GLMM will converge without singular fit issues for the available sample size (minimum N determined by power analysis per FR-015)
- CoNet network construction will complete within reasonable time for ≤100 samples
- All statistical analyses (diversity computation, model fitting, ANCOM-BC, permutation tests) can execute in default precision without GPU acceleration
- QIIME 2 and CoNet tools can be containerized in a Docker image ≤2 GB for reproducible execution
- Observational design precludes causal claims; all findings will be framed as associational relationships per FR-009
- **Design Parameters**: Target is to attempt retrieval of ≥100 samples. If <30 matched samples are found, the system MUST halt and report a Feasibility Report. **No synthetic data fallback is allowed.**
- **Effect Size Assumption**: The power analysis (FR-015) uses an effect size assumption of 0.1 based on community standards for ecological effect sizes. If real data variance is available, it will be used instead.
- **Prohibition on Synthetic Data**: The use of synthetic or randomly generated disease labels for hypothesis testing is explicitly prohibited. If real data is unavailable, the system MUST NOT proceed with model fitting. Code validation (unit tests) may use dummy data but MUST NOT produce scientific findings.
- **Invalid Join Strategy**: The system MUST NOT attempt to join disparate datasets (e.g., EMP soil data + generic GPS data) via metadata, as this approach cannot answer the research question.