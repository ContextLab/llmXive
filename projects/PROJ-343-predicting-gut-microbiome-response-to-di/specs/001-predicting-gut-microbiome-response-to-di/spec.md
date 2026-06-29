# Feature Specification: Predicting Gut Microbiome Response to Dietary Interventions

**Feature Branch**: `001-predicting-gut-microbiome-response`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Predict baseline gut microbial composition that determines the magnitude of taxonomic shift following a high‑fiber dietary intervention in healthy adults using publicly available 16S data."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑end Prediction Pipeline (Priority: P1)

A researcher wants to run a reproducible, CPU‑only pipeline that downloads public 16S data, processes it, and outputs a trained model predicting the microbiome response to a fiber intervention.

**Why this priority**: It delivers the core scientific value—producing the predictive map that addresses the research gap.

**Independent Test**: Execute the pipeline on the American Gut dataset alone; verify that a model file and performance report are generated without manual intervention.

**Acceptance Scenarios**:

1. **Given** a list of study accession IDs, **when** the pipeline is invoked, **then** it downloads all raw FASTQ files and associated metadata to a designated workspace.  
2. **Given** the downloaded data, **when** the pipeline finishes processing, **then** it outputs (a) a CSV of baseline diversity metrics, (b) a CSV of genus‑level abundances, (c) a trained Random Forest model file, and (d) a performance report containing cross‑validated R².

### User Story 2 – Model Evaluation Dashboard (Priority: P2)

A researcher wants to quickly assess which baseline taxa drive the predicted response and how well the model performs.

**Why this priority**: Enables interpretation of results and informs downstream experimental design.

**Independent Test**: Run the pipeline, then launch the dashboard; verify that feature‑importance bar plots and a predicted‑vs‑observed scatter plot appear.

**Acceptance Scenarios**:

1. **Given** a completed pipeline run, **when** the researcher opens the HTML dashboard, **then** the dashboard displays (a) the most important taxa ranked by importance, (b) the cross‑validated R² value, (c) a scatter plot with a regression line and a **95% confidence interval derived from 1000 bootstrap resamples**.

### User Story 3 – Export & Reproducibility Package (Priority: P3)

A researcher wants to export all results, figures, and code to a public repository for peer review and reuse.

**Why this priority**: Aligns with open‑science requirements and ensures reproducibility.

**Independent Test**: After a successful run, invoke the export command; verify that a zip archive containing data, figures, the model, and a README is produced.

**Acceptance Scenarios**:

1. **Given** a completed analysis, **when** the researcher runs the export utility, **then** a `gut_microbiome_prediction_<date>.zip` file is created containing (i) processed data tables, (ii) PNG/SVG figures, (iii) the serialized model (`.pkl`), and (iv) a reproducibility README with environment specifications.

### Edge Cases

- **Missing Metadata**: If a sample lacks a recorded dietary‑intervention label, the system excludes the sample and records the omission in a log file.  
- **Insufficient Reads**: Samples with fewer than **[deferred] reads** after quality filtering are excluded and logged; the pipeline continues with remaining samples.
- **Zero Response**: When pre‑and post‑intervention compositions are identical (Aitchison distance = 0), the sample is retained; the model receives a response value of 0 and treats it as valid data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw 16S rRNA FASTQ files and associated metadata from the American Gut Project and any additional public repositories given a list of accession identifiers.  
- **FR-002**: System MUST filter samples to retain only participants with both pre‑intervention and post‑intervention records for a high‑fiber dietary change.  
- **FR-003**: System MUST filter sequences with QIIME2/DADA2, performing quality filtering, denoising, and **subsampling to [deferred] reads per sample**, while never exceeding **7 GB RAM** on a single CPU node.
- **FR-004**: System MUST compute baseline diversity metrics (Shannon index, Faith's Phylogenetic Diversity) **AND genus‑level relative abundances** for each retained sample. These metrics constitute the predictor features for model training. (See US-1)  
- **FR-005**: System MUST define the response variable as the **Aitchison distance** (Euclidean distance after centered log‑ratio transformation) between pre‑ and post‑intervention CLR‑transformed genus‑level composition vectors. Prior to CLR transformation, a **pseudocount of 1 × 10⁻⁶** is added to all taxa counts to handle zeros. The model is a **Random Forest regressor** (scikit‑learn, CPU‑only) trained on baseline features comprising Shannon diversity, Faith's PD, **and genus‑level relative abundances**, using **5‑fold cross‑validation** and a modest hyper‑parameter grid: `n_estimators ∈ {100, 200, 500}` and `max_features ∈ {"sqrt", "log2"}`. Aitchison/CLR is used because microbiome data are compositional; see Gloor et al., 2017 for justification. (See US-1)  
- **FR-006**: System MUST perform **1000‑iteration permutation testing** to generate a null distribution of R² values and report a permutation‑adjusted p‑value.  
- **FR-007**: System MUST generate a concise HTML dashboard summarizing (a) model performance (cross‑validated R², permutation p‑value), (b) top 10 predictive taxa with importance scores, and (c) a predicted‑vs‑observed scatter plot with a regression line and a **95% confidence interval derived from 1000 bootstrap resamples**. (See US-2)  
- **FR-008**: System MUST bundle all processed data, figures, model artefacts, and a reproducibility README into a single exportable archive. (See US-3)  
- **FR-009**: System MUST replace zero counts in genus‑level count tables with a pseudocount of **1 × 10⁻⁶** before performing CLR transformation. (See US-1)  
- **FR-010**: System MUST handle samples with insufficient reads (**< 10,000**) by excluding them from analysis, recording their identifiers in a log file, and continuing without termination. (See US-1)  
- **FR-011**: System MUST handle samples missing dietary‑intervention metadata by excluding them, recording the omission in a log file, and continuing execution. (See US-1)  
- **FR-012**: System MUST retain samples whose computed Aitchison distance equals 0 (zero response) and include them in model training; such samples are flagged in the results but do not cause errors. (See US-1)  
- **FR-013**: System MUST adjust for known confounding variables (age, medication use, baseline diet) by including them as covariates in the model, to reduce bias in the predictive relationship. (See US-1)

### Key Entities *(include if feature involves data)*

- **Sample**: Represents an individual gut microbiome sequencing run; key attributes – `sample_id`, `subject_id`, `timepoint` (pre/post), `dietary_intervention` (high‑fiber vs. control), `raw_reads_path`.  
- **BaselineFeatureSet**: Aggregated baseline metrics for a subject; attributes – `shannon`, `faith_pd`, `genus_abundances` (relative abundance per genus).  
- **ResponseMetric**: Aitchison distance value quantifying compositional shift between paired timepoints.  
- **ModelArtifact**: Serialized Random Forest model file (`.pkl`) together with hyper‑parameters and training metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cross‑validated **R² ≥ 0.10** on the primary American Gut cohort. (See US-1)  
- **SC-002**: Permutation test yields a **p‑value < 0.05** when comparing the model's R² to the null distribution, and the same significance is achieved on **at least two** independent public cohorts (e.g., additional American Gut subsets or other open‑access 16S studies), with **FDR correction (Benjamini‑Hochberg, q ≤ 0.05)** applied across multiple cohort tests to control Type I error. (See US-1)  
- **SC-003**: End‑to‑end pipeline completes within **48 hours** on a single CPU node with ≤ 7 GB RAM for a dataset of ≤ 200 paired samples. (See US-1)  
- **SC-004**: Generated HTML dashboard loads in **≤ 5 seconds** measured on a machine with an Intel i5‑10400 CPU @ 2.9 GHz, 8 GB RAM, SSD storage, running Ubuntu 22.04, using Chrome 119 in incognito mode with cache cleared and no network activity (local file load over loopback). (See US-2)  
- **SC-005**: Exported reproducibility archive contains all required artefacts and passes a checksum‑based integrity test (MD5 match) on the receiving end. (See US-3)

## Assumptions

- Public datasets provide **accurate, machine‑readable metadata** indicating dietary intervention type and sampling timepoints.  
- "High‑fiber dietary intervention" is consistently defined across studies as **≥ 25 g fiber/day** for at least **2 weeks**; if definitions vary, the pipeline will use the study‑reported label without transformation.  
- The subsampling depth of **[deferred] reads per sample** is applied uniformly; samples with fewer reads are excluded (see FR‑010).
- Zero counts in taxonomic tables are replaced with a **pseudocount of 1 × 10⁻⁶** prior to CLR transformation to enable Aitchison distance computation.  
- The Euclidean distance on genus‑level relative abundances is replaced by the **Aitchison distance** after a centered log‑ratio (CLR) transformation, adhering to compositional data analysis best practices (Gloor et al. 2017). This is scientifically preferred over raw Euclidean distance because microbiome data are compositional (relative abundances summing to 1), and CLR transformation removes the spurious correlation problem inherent in compositional data.  
- Baseline predictor features consist of Shannon diversity, Faith's Phylogenetic Diversity, **and** genus‑level relative abundances to capture compositional information required for prediction (see FR‑004 and FR‑005).  
- Sufficient computational resources (single CPU core, ≤ 7 GB RAM) are available on the execution environment.  
- Researchers have basic familiarity with Python, Conda environments, and command‑line execution.  
- No protected health information (PHI) is present in the public datasets; thus, GDPR/HIPAA compliance is not required for this pipeline.  
- The Random Forest implementation from scikit‑learn (v 1.5 or later) is acceptable for baseline modeling; hyper‑parameter tuning is limited to the modest grid described in FR‑005.  
- Known confounders (age, medication, baseline diet) are available in metadata and can be adjusted for in the model (see FR‑013).
