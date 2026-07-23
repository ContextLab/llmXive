# Feature Specification: Predicting Plant Pathogen Virulence from Publicly Available Genomic and Phenotypic Data

**Feature Branch**: `001-predict-plant-pathogen-virulence`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Plant Pathogen Virulence from Publicly Available Genomic and Phenotypic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducible Data Pipeline Execution (Priority: P1)

A researcher can execute a fully automated pipeline that downloads specific plant pathogen genomes (*Fusarium graminearum*, *Pseudomonas syringae*, *Xanthomonas* spp.) from NCBI, extracts virulence-associated gene presence/absence and transcription factor binding sites, and retrieves linked phenotypic disease severity scores from curated literature tables or species-level aggregations, resulting in a clean, merged analysis-ready dataset.

**Why this priority**: This is the foundational capability. Without a reliable, reproducible data ingestion and feature extraction pipeline, no statistical analysis can occur. It delivers the primary value of bridging the gap between isolated genomic and phenotypic datasets.

**Independent Test**: The pipeline can be run end-to-end on a clean environment; it must produce a single CSV/Parquet file containing aligned genomic feature vectors and phenotypic scores for at least 10 distinct isolates (or species aggregates if isolate-level data is unavailable), with all source URLs logged.

**Acceptance Scenarios**:

1. **Given** a list of target pathogen taxa, **When** the data ingestion script runs, **Then** it successfully downloads genome assemblies via NCBI E-utilities and phenotype data from curated tables (e.g., PHI-base phenotype sheets) or species-level aggregations without manual intervention.
2. **Given** downloaded genome assemblies, **When** the feature extraction module runs, **Then** it generates a binary matrix for virulence gene presence/absence (using PHI-base/Pfam) and a matrix for TF binding site counts, merging them with the phenotypic data by isolate ID or species ID.
3. **Given** the merged dataset, **When** the pipeline completes, **Then** it outputs a summary report listing the number of isolates processed, the number of features extracted, and the number of missing phenotypic values, with a fallback to species-level aggregation if isolate-level linkage fails.

---

### User Story 2 - Statistical Association Analysis (Priority: P2)

A researcher can run a statistical analysis on the prepared dataset to compute Phylogenetic Generalized Least Squares (PGLS) correlations between genomic features and phenotypic virulence scores, applying permutation-based multiple testing corrections to identify statistically significant associations while controlling for phylogenetic non-independence.

**Why this priority**: This delivers the core scientific insight. It transforms the raw data into testable hypotheses about which genomic features predict virulence, directly addressing the research question while correcting for shared ancestry.

**Independent Test**: The analysis script runs on the P1 output dataset and produces a ranked list of genomic features with correlation coefficients, p-values, and adjusted p-values, identifying a set of top candidates.

**Acceptance Scenarios**:

1. **Given** the analysis-ready dataset and a phylogenetic tree, **When** the correlation analysis runs, **Then** it calculates PGLS correlation coefficients for every genomic feature against the disease severity score.
2. **Given** the raw p-values from the PGLS tests, **When** the multiple testing correction step runs, **Then** it applies a permutation-based FDR correction (or Benjamini-Yekutieli) to control the False Discovery Rate (FDR) at < 0.05.
3. **Given** the corrected p-values, **When** the results are generated, **Then** the system outputs a table of ALL features where the adjusted p-value < 0.05, regardless of effect size, marking them as "statistically significant."

---

### User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

A researcher can view a visualization of the top genomic-virulence associations (heatmap or scatter plots) and access a self-contained Jupyter notebook that documents the entire workflow, ensuring the results are reproducible and interpretable.

**Why this priority**: This ensures the results are communicable and verifiable. It completes the research loop by providing the visual evidence and the executable context required for peer review or breeding program adoption.

**Independent Test**: The pipeline generates a PNG heatmap of the top significant features and a `.ipynb` file that, when opened, renders the analysis steps and plots without requiring additional configuration.

**Acceptance Scenarios**:

1. **Given** the list of significant genomic features, **When** the visualization module runs, **Then** it generates a seaborn heatmap showing the correlation strength of the top 10 features (filtered by |ρ| ≥ 0.5) against disease severity.
2. **Given** the full analysis workflow, **When** the documentation step runs, **Then** it compiles a Jupyter notebook containing all code, data source URLs, and parameter settings used in the analysis.
3. **Given** the generated artifacts, **When** a user opens the notebook, **Then** all cells execute successfully on a standard CPU environment, reproducing the statistical tables and figures with numerical equivalence within a tolerance of a sufficiently small threshold.

### Edge Cases

- **What happens when** the public datasets (NCBI/OpenML) are temporarily unavailable or rate-limited? The system must implement exponential backoff retries (a limited number of attempts) and log the specific error before failing gracefully.
- **How does the system handle** isolates that exist in the genomic database but lack linked phenotypic severity scores? These rows must be excluded from the correlation analysis but reported in the summary statistics as "excluded due to missing phenotype."
- **What happens when** a specific pathogen isolate has no annotated virulence genes in PHI-base? The feature extraction must assign a zero vector for those features rather than crashing, treating "absence of annotation" as "absence of feature" for the correlation.
- **What happens when** isolate-level phenotypic linkage is impossible? The system must automatically fallback to aggregating data at the species level and report the analysis as "Species-level aggregate analysis" rather than "Isolate-level analysis."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download genome assemblies for *Fusarium graminearum*, *Pseudomonas syringae*, and *Xanthomonas* spp. from NCBI using E-utilities and retrieve phenotypic disease severity scores from curated literature tables (e.g., PHI-base) or species-level aggregations (See US-1).
- **FR-002**: System MUST extract virulence-associated gene presence/absence profiles using `hmmsearch` against PHI-base and Pfam domain libraries, and count transcription factor binding sites using position weight matrices (See US-1).
- **FR-003**: System MUST construct or retrieve a phylogenetic tree for the input isolates using core genes or 16S sequences to enable phylogenetic correction (See US-2).
- **FR-004**: System MUST compute Phylogenetic Generalized Least Squares (PGLS) correlation coefficients between every extracted genomic feature and the phenotypic disease severity score vector, controlling for phylogenetic non-independence (See US-2).
- **FR-005**: System MUST apply a permutation-based FDR correction (or Benjamini-Yekutieli) to correct for multiple hypothesis testing, ensuring a False Discovery Rate (FDR) of < 0.05 (See US-2).
- **FR-006**: System MUST handle missing phenotypic data by excluding the affected rows from analysis and logging the exclusion count, without failing the pipeline execution (See US-1).
- **FR-007**: System MUST filter the output of statistically significant features (FDR < 0.05) by effect size (|ρ| ≥ 0.5) specifically for visualization purposes, while retaining all significant features in the raw output (See US-2, US-3).
- **FR-008**: System MUST generate a reproducible Jupyter notebook and a static heatmap visualization of the top significant associations (correlation ≥ 0.5, FDR < 0.05) (See US-3).
- **FR-009**: System MUST fallback to species-level aggregation analysis if isolate-level phenotypic linkage fails for > 50% of the target taxa (See US-1).
- **FR-010**: System MUST pin all Python dependencies in a `requirements.txt` file with exact versions to ensure numerical reproducibility (See US-3).

### Key Entities

- **Isolate**: A unique biological sample identified by a specific strain ID, containing linked genomic sequence data and a quantitative disease severity score (if available).
- **Species Aggregate**: A grouped dataset where phenotypic scores are averaged across multiple isolates of the same species to enable analysis when isolate-level linkage is unavailable.
- **Genomic Feature**: A binary indicator (presence/absence) of a virulence gene or a quantitative count of transcription factor binding sites within a specific genomic region.
- **Phenotypic Score**: A numerical value (0.0 to 1.0 or similar scale) representing the observed disease severity for a specific isolate or species aggregate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Success rate = (processed isolates or species aggregates / requested taxa) * [deferred] must be ≥ 90% (See US-1).
- **SC-002**: The False Discovery Rate (FDR) of the reported significant associations is measured against the permutation-based threshold. to ensure statistical validity (See US-2).
- **SC-003**: The reproducibility of the analysis is measured by the successful execution of the generated Jupyter notebook on a clean CPU-only environment, producing correlation coefficients and p-values numerically equivalent within a tolerance of a sufficiently small threshold (See US-3).
- **SC-004**: The proportion of significant features (FDR < 0.05) with an absolute correlation coefficient |ρ| ≥ 0.5 must be reported (See US-2).
- **SC-005**: Pipeline runtime must be ≤ 6 hours and peak memory usage ≤ 7 GB (See US-1).

## Assumptions

- **Dataset-variable fit**: Public datasets (NCBI, PHI-base) may not contain isolate-level phenotypic scores linked to specific genome assemblies. The system assumes that species-level aggregates or curated literature tables can serve as a valid proxy for virulence profiling. If isolate-level linkage is impossible, the analysis defaults to species-level aggregation.
- **Inference framing**: All findings are framed as **associational** correlations, not causal effects, as the data is observational with no random assignment of genomic features to isolates.
- **Compute constraints**: The analysis assumes that the selected pathogen genomes and feature matrices will fit within the standard RAM limits of a CI runner; if the dataset is larger, a sampling strategy or subset selection will be applied.
- **Threshold justification**: The correlation threshold of |ρ| ≥ 0.5 is selected based on common practice in genomic association studies to filter for moderate-to-strong effects, and a sensitivity analysis sweeping the threshold across a range of values will be performed to validate stability.
- **Measurement validity**: The virulence gene annotations rely on the completeness of the PHI-base and Pfam databases; new or uncharacterized virulence factors may not be detected.
- **Predictor collinearity**: Genomic features are highly collinear; the analysis uses permutation-based FDR correction to account for this dependency structure.
- **Phylogenetic correction**: A reference phylogenetic tree can be constructed from core genes or retrieved from public databases (e.g., NCBI Taxonomy) for the target species.
- **No GPU requirement**: The analysis relies entirely on CPU-tractable statistical methods (PGLS, permutation testing) and does not require deep learning models, GPU acceleration, or 8-bit quantization.