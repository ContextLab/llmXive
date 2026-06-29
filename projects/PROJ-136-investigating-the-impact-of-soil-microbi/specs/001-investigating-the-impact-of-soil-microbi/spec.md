# Feature Specification: Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance

**Feature Branch**: `001-soil-microbiome-diversity-disease-resistance`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Soil Microbiome Diversity on Plant Disease Resistance"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

Researcher downloads processed 16S rRNA amplicon tables from Earth Microbiome Project (EMP) agricultural subset or MG-RAST soil microbiome repository, obtains plant disease incidence records from published agricultural soil microbiome studies with matched metadata (plant species, GPS coordinates, soil type, disease incidence rate), and retrieves associated metadata from study metadata files. The data is filtered (OTU/ASV tables to retain taxa present in ≥5% of samples), rarefied to uniform sequencing depth, and disease incidence data is aligned with matching soil samples via location and date fields.

**Why this priority**: Without clean, aligned data from both sources, no downstream analysis can proceed. This is the foundational data layer that enables all statistical modeling and hypothesis testing.

**Independent Test**: Can be fully tested by verifying that the downloaded dataset contains sufficient samples for downstream analysis, disease records contain disease incidence entries, and the merged dataset has matched samples with complete metadata (plant species, GPS, soil type, disease incidence rate).

**Acceptance Scenarios**:

1. **Given** MG-RAST and Qiita agricultural soil microbiome data sources are accessible, **When** researcher executes data download scripts, **Then** ≥100 EMP/MG-RAST samples and ≥50 disease incidence records are retrieved with ≥30 matched samples containing complete metadata
2. **Given** raw OTU/ASV tables contain taxa with <5% prevalence, **When** filtering is applied, **Then** only taxa present in ≥5% of samples are retained and rarefied to a sufficiently low read depth per sample

---

### User Story 2 - Statistical Analysis and Model Fitting (Priority: P2)

Researcher computes alpha-diversity metrics (Shannon, Simpson, Faith's PD) per sample using QIIME 2's `diversity alpha` plugin, then fits beta regression or binomial generalized linear mixed-effects models (GLMM) with disease incidence as response (proportion data), alpha diversity as fixed effect, and random intercepts for plant species and geographic region. The diversity coefficient significance (p<0.05) and effect size are reported, with permutation tests (10,000 permutations) confirming observed correlations exceed random expectations. Additionally, the researcher performs stratified analysis by crop type subset (as required by robustness section) to assess whether the diversity-disease relationship holds across different agricultural contexts, reporting consistency of effect direction and magnitude across subsets.

**Why this priority**: This is the core research hypothesis test that directly answers the research question. Without valid statistical models, no conclusions about microbiome diversity and disease resistance can be drawn. The crop subset analysis addresses the robustness requirement from the original idea.

**Independent Test**: Can be fully tested by running the statistical analysis pipeline on a subset of 30 matched samples and verifying that a beta regression or binomial GLMM produces a p-value for the diversity coefficient, that permutation test results are reproducible, and that crop subset stratification produces consistent effect directions.

**Acceptance Scenarios**:

1. **Given** ≥30 matched samples with computed alpha-diversity metrics, **When** beta regression or binomial GLMM is fitted with disease incidence as response, **Then** diversity coefficient p-value <0.05 (or null result reported) with effect size and 95% confidence interval
2. **Given** observed correlation coefficient, **When** Multiple permutation tests are executed, **Then** p-permutation <0.05 confirming correlation exceeds random expectations
3. **Given** samples stratified by crop type into ≥2 subsets, **When** diversity-disease model is fitted per subset, **Then** effect direction (positive/negative) is consistent across ≥80% of subsets with effect sizes within same order of magnitude

---

### User Story 3 - Keystone Taxon Identification and Network Analysis (Priority: P3)

Researcher performs differential abundance testing (ANCOM) between high- and low-disease sites to highlight taxa enriched in disease-suppressed soils, then constructs co-occurrence networks (CoNet) and computes node centrality. Taxa with high betweenness/degree are flagged as putative keystones.

**Why this priority**: This provides mechanistic insight beyond the diversity-level correlation, identifying specific taxa that may drive disease suppression. It is secondary to establishing the core diversity-disease relationship.

**Independent Test**: Can be fully tested by running ANCOM on a subset of samples and verifying that ≥3 taxa are identified with differential abundance (q<0.1) and that co-occurrence network produces ≥10 nodes with centrality metrics computed.

**Acceptance Scenarios**:

1. **Given** samples stratified into high/low disease groups, **When** ANCOM is executed, **Then** ≥3 taxa are identified with differential abundance (q<0.1) enriched in disease-suppressed soils
2. **Given** ≥30 samples with taxonomic composition, **When** CoNet co-occurrence network is constructed, **Then** ≥10 nodes have betweenness/degree centrality computed and ≥2 taxa flagged as putative keystones

---

### Edge Cases

- What happens when EMP/MG-RAST and disease datasets cannot be matched via location and date fields (fewer than 30 matched samples)?
- How does system handle when sequencing depth varies widely (>10x difference) and rarefaction discards >50% of reads?
- What happens when beta regression or binomial GLMM fails to converge (singular fit, boundary issues)?
- How does system handle when ANCOM differential abundance testing produces no significant taxa (q≥0.1 for all)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download 16S rRNA amplicon tables from Earth Microbiome Project agricultural subset or MG-RAST soil microbiome repository with ≥100 samples retained after filtering (See US-1)
- **FR-002**: System MUST rarefy OTU/ASV tables to uniform sequencing depth of 10k reads per sample using QIIME 2 (See US-1)
- **FR-003**: System MUST compute alpha-diversity metrics (Shannon, Simpson, Faith's PD) per sample using QIIME 2's `diversity alpha` plugin (See US-2)
- **FR-004**: System MUST fit beta regression or binomial generalized linear mixed-effects models with disease incidence (proportion 0-100%) as response, alpha diversity as fixed effect, and random intercepts for plant species and geographic region (See US-2)
- **FR-005**: System MUST conduct permutation tests with a sufficient number of permutations to confirm observed correlations exceed random expectations (See US-2)
- **FR-006**: System MUST perform differential abundance testing (ANCOM) between high- and low-disease sites to identify taxa enriched in disease-suppressed soils (See US-3)
- **FR-007**: System MUST construct co-occurrence networks (CoNet) and compute node centrality (betweenness/degree) for keystone taxon identification (See US-3)
- **FR-008**: System MUST verify that EMP/MG-RAST dataset contains required variables: OTU/ASV tables, plant species, GPS coordinates, soil type, sequencing depth. System MUST verify that disease dataset contains required variables: sample ID, disease type, incidence rate (0-100%), measurement date. If any variable is missing, record explicit [MISSING_VARIABLE: <variable-name>] marker with count of affected samples (See US-1)
- **FR-009**: System MUST frame all statistical findings as ASSOCIATIONAL (not causal) since no random assignment exists in observational design (See US-2)
- **FR-010**: System MUST apply multiple-comparison / family-wise-error correction when >1 hypothesis test is run (See US-2)
- **FR-012**: System MUST diagnose predictor collinearity when two predictors are definitionally related and frame joint relationships descriptively (See US-2)
- **FR-015**: System MUST conduct a priori power analysis (power ≥0.8) to determine minimum sample size for detecting diversity effect on disease incidence with effect size ≥0.1 (See US-2)

### Key Entities

- **Sample**: Represents a single soil microbiome collection with attributes: sample ID, GPS coordinates, plant species, soil type, sequencing depth, alpha-diversity metrics
- **Disease Incidence**: Represents plant disease measurement with attributes: sample ID, disease type, incidence rate (0-100%), measurement date
- **Taxon**: Represents microbial taxonomic unit with attributes: taxon ID, taxonomic lineage, relative abundance, differential abundance q-value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation coefficient between alpha-diversity (Shannon/Simpson) and disease incidence is measured against published meta-analysis values from soil microbiome-disease literature (See US-2)
- **SC-002**: Model fit statistics (R², AIC) for beta regression/GLMM are measured against null model baseline (See US-2)
- **SC-003**: Number of keystone taxa identified with differential abundance (q<0.1) is measured against ANCOM output (See US-3)
- **SC-004**: Permutation test p-value stability is measured across multiple independent runs with sufficient permutations (See US-2)
- **SC-005**: Multiple-comparison correction applied rate is measured against total hypothesis tests run (≥100% correction coverage required) (See US-2)
- **SC-006**: Data acquisition quality is measured against EMP/MG-RAST agricultural subset availability, disease dataset completeness, and matched sample count (See US-1)

## Assumptions

- EMP agricultural subset and MG-RAST soil microbiome data sources remain accessible and unchanged during the analysis window
- ≥30 matched samples with complete metadata can be obtained from the intersection of soil microbiome and disease incidence datasets
- Beta regression or binomial GLMM will converge without singular fit issues for the available sample size (minimum N determined by power analysis per FR-015)
- CoNet network construction will complete within reasonable time for ≤100 samples
- All statistical analyses (diversity computation, model fitting, ANCOM, permutation tests) can execute in default precision without GPU acceleration
- QIIME 2 and CoNet tools can be containerized in a Docker image ≤2 GB for reproducible execution
- No missing variables exist in EMP/MG-RAST/disease datasets for the required predictors (alpha diversity), outcome (disease incidence), and covariates (plant species, soil type, geography); if gaps exist, [MISSING_VARIABLE] markers will be recorded per FR-008
- Observational design precludes causal claims; all findings will be framed as associational relationships per FR-009
- Empirical targets (≥100 samples, ≥50 disease records, ≥30 matched samples, 10k reads) are deferred to implementation phase as per planning guidance
- Crop subset stratification will yield ≥2 subsets with sufficient samples (≥15 per subset) for meaningful comparison