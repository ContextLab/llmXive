# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Circadian Rhythm Disruption

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Circadian Rhythm Disruption in Publicly Available Datasets"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Cohort Definition (Priority: P1)

The system must successfully download, merge, and filter the American Gut Project microbiome data and Open Humans sleep survey metadata to produce a clean, analysis-ready dataset containing only participants with valid data in both domains.

**Why this priority**: Without a valid, merged cohort, no statistical analysis can occur. This is the foundational step that determines the sample size (N) and data quality for the entire study.

**Independent Test**: The pipeline can be run in isolation to verify that it outputs a single CSV/TSV file where row counts match the intersection of valid microbiome and sleep records, and all required columns (Shannon diversity, sleep duration, chronotype, covariates) are present and non-null.

**Acceptance Scenarios**:

1. **Given** the raw American Gut and Open Humans datasets are available, **When** the ingestion script executes, **Then** a merged dataset is produced and the system reports the exact participant count N. If N ≥ 200, the system proceeds; if N < 200, the system flags a power limitation in the report and proceeds with the available sample size.
2. **Given** a participant has missing data for either microbiome or sleep metrics, **When** the filter step runs, **Then** that participant is excluded from the final analysis cohort.
3. **Given** the merged dataset, **When** a summary report is generated, **Then** it lists the exact count of retained participants and the distribution of key covariates (age, BMI, antibiotic use).

### User Story 2 - Associational Analysis and Visualization (Priority: P2)

The system must compute alpha/beta diversity metrics, perform correlation testing against sleep metrics with FDR correction, and generate visualizations (heatmaps, PCoA plots) to display the strength and direction of associations.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by quantifying the relationship between microbiome diversity and circadian disruption while controlling for confounders.

**Independent Test**: The analysis module can be executed on the cleaned dataset to produce a results table of correlation coefficients (rho) and p-values, along with static image files of the required plots, without requiring interactive user input.

**Acceptance Scenarios**:

1. **Given** the cleaned cohort dataset, **When** the analysis script runs, **Then** it outputs a table of Spearman/Pearson correlations and distance-based redundancy analysis (dbRDA) results between diversity metrics (Shannon, Simpson) and sleep variables (duration, quality, chronotype) with FDR-corrected p-values.
2. **Given** the analysis results, **When** the visualization module runs, **Then** it generates a heatmap of taxa-sleep associations and a PCoA plot colored by sleep quality scores.
3. **Given** the multivariate regression model, **When** executed, **Then** it outputs adjusted effect sizes that explicitly state the association is correlational, not causal, for all reported findings.

### User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

The system must validate the stability of observed correlations via bootstrap resampling and perform a sensitivity analysis on any decision thresholds (e.g., significance cutoffs) to ensure results are not artifacts of specific parameter choices.

**Why this priority**: This ensures the scientific rigor of the findings, addressing concerns about overfitting and threshold sensitivity, which are critical for the methodological soundness of the study.

**Independent Test**: The validation script can be run to produce a secondary set of results on bootstrap resamples and a sensitivity report showing how results change when the significance threshold is varied.

**Acceptance Scenarios**:

1. **Given** the full dataset, **When** the bootstrap resampling runs (1000 iterations), **Then** the system calculates 95% confidence intervals for the top 5 correlations (selected by absolute effect size, breaking ties by lowest p-value). The system passes if the confidence intervals for these top 5 do not include zero.
2. **Given** a primary significance threshold (e.g., p < 0.05), **When** the sensitivity analysis runs, **Then** it reports how the number of significant taxa changes when the threshold is swept across {0.01, 0.05, 0.1}.
3. **Given** the final results, **When** the report is generated, **Then** it includes a specific section detailing the stability of findings (bootstrap CIs) and the sensitivity sweep.

### Edge Cases

- What happens when the intersection of American Gut and Open Humans data yields fewer than 200 participants? The system must flag this as a power limitation in the report and proceed with the available sample size, explicitly noting the reduced statistical power.
- How does the system handle participants with extreme outliers in sleep duration (e.g., < 2 hours or > 16 hours)? The system must cap these values at extreme percentiles of the distribution (1st/99th) or exclude them, documenting the exclusion criteria.
- How does the system handle missing covariate data (e.g., BMI or antibiotic history)? The system must impute missing values using median/mode for continuous/categorical variables or exclude the participant if >20% of covariates are missing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse 16S rRNA data from the American Gut Project and sleep metadata from Open Humans, merging them on participant ID to create a unified dataset. (See US-1)
- **FR-002**: System MUST calculate alpha diversity (Shannon, Simpson) and beta diversity (Bray-Curtis) metrics for each participant in the merged cohort. (See US-2)
- **FR-003**: System MUST perform Spearman/Pearson correlation tests AND distance-based redundancy analysis (dbRDA) between diversity metrics and sleep variables, applying Benjamini-Hochberg FDR correction to all p-values. The system MUST also report the correlation between alpha and beta diversity metrics to account for their mathematical coupling. (See US-2)
- **FR-004**: System MUST execute a Generalized Linear Model (GLM) with appropriate distribution (Gaussian with log-link for diversity, ordinal logistic for chronotype) or PERMANOVA for beta diversity to adjust for confounders (age, BMI, diet timing, medication, antibiotic history) and report adjusted association coefficients. (See US-2)
- **FR-005**: System MUST generate a heatmap of taxa-sleep associations and a PCoA ordination plot colored by sleep quality scores. (See US-2)
- **FR-006**: System MUST perform bootstrap resampling (1000 iterations) to estimate 95% confidence intervals for correlation coefficients. If the cohort size N < 40, the system MUST skip resampling and proceed with full-dataset analysis, flagging the limitation. (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis sweeping the significance threshold over a range of conventional values and report the variation in significant taxa counts. (See US-3)
- **FR-008**: System MUST output all results in a human-readable report format that explicitly frames findings as associational, avoiding causal language. (See US-2)

### Key Entities

- **Participant**: A human subject with linked microbiome sequencing data and sleep survey responses.
- **DiversityMetric**: A quantitative measure of microbiome richness/evenness (e.g., Shannon index) calculated per participant.
- **SleepVariable**: A self-reported metric of circadian rhythm disruption (e.g., sleep duration, quality score, chronotype).
- **Covariate**: A potential confounding variable (e.g., age, BMI, antibiotic use) used in regression adjustment.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of participants retained in the final cohort is measured against the minimum threshold of N=200 required for adequate statistical power. (See US-1)
- **SC-002**: The stability of correlation coefficients is measured by the 95% confidence intervals derived from 1000 bootstrap resamples. The criterion is met if the confidence intervals for the top 5 associations (by absolute effect size) do not include zero. (See US-3)
- **SC-003**: The robustness of significant findings is measured against the variation in significant taxa counts when the p-value threshold is swept across {0.01, 0.05, 0.1}. (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of completing the entire pipeline within 6 hours on a GitHub Actions 2-core runner with 7 GB RAM, tested on a dataset of N=200 participants. (See US-2)
- **SC-005**: The methodological soundness is measured by the presence of FDR correction, non-linear screening (dbRDA), and explicit associational framing in the final output, verified by the absence of causal language in the results section. (See US-2)

## Assumptions

- The American Gut Project and Open Humans datasets contain the necessary variables (16S rRNA sequences, sleep duration, quality, chronotype, age, BMI, diet timing, medication history) for the proposed analysis.
- The American Gut Project data includes 16S rRNA sequences processed to a level of resolution sufficient for calculating alpha and beta diversity metrics (e.g., OTU or ASV tables).
- The sleep metrics from Open Humans are self-reported and valid proxies for circadian rhythm disruption, despite potential recall bias.
- The computational resources available (GitHub Actions 2-core runner, 7 GB RAM) are sufficient to process the merged dataset (N ≥ 200) and run the specified statistical tests (correlation, GLM, bootstrap) within the 6-hour limit.
- The American Gut Project and Open Humans data can be legally and technically accessed and merged without violating privacy or terms of service.
- The relationship between gut microbiome and circadian rhythm may be non-linear; therefore, the analysis includes non-parametric screening (dbRDA) to capture complex associations.
- The confounders (age, BMI, diet, medication) are adequately captured in the survey data to allow for effective multivariate adjustment via GLM.
- The FDR correction method (Benjamini-Hochberg) is appropriate for the number of hypotheses tested in this study.