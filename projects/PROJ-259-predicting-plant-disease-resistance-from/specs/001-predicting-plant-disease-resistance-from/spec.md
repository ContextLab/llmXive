# Feature Specification: Predict Plant Disease Resistance from Multi‑omics Data

**Feature Branch**: `001-predict-plant-disease-resistance`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: “Can plant disease resistance be predicted using publicly available genomic (SNPs) and metabolomic data from plant‑pathogen interaction studies? Identify genetic markers and metabolic signatures that correlate with resistance levels, with statistical validation (p < 0.05 after multiple testing correction) and cross‑validation accuracy ≥ 75 %.”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑End Resistance Prediction (Priority: P1)

A plant‑biology researcher wants to run a reproducible pipeline that downloads public genotype and metabolomics data, preprocesses them, selects predictive features, trains a model, and reports performance metrics.

**Why this priority**: This story delivers the core scientific value – a demonstrable predictive model – and is required before any downstream interpretation can occur.

**Independent Test**: Execute the pipeline on a selected public dataset and verify that it completes, produces a trained model, and outputs the required performance metrics without manual intervention.

**Acceptance Scenarios**:

1. **Given** a plant species name and a list of public repository identifiers, **when** the pipeline is invoked, **then** it downloads the raw data, preprocesses them, and creates aligned SNP and metabolite matrices with matching resistance phenotypes.  
2. **Given** the preprocessed feature tables, **when** the model training step finishes, **then** cross‑validated accuracy (or AUC‑ROC / R²) is reported and meets the ≥ 75 % threshold.

---

### User Story 2 – Biomarker Exploration (Priority: P2)

A researcher wants to examine which SNPs and metabolites drive the model’s predictions and assess their statistical significance.

**Why this priority**: Understanding the biological basis of predictions is essential for downstream breeding applications and scientific insight.

**Independent Test**: After a successful run of Story 1, query the pipeline’s output for the ranked list of selected features and verify that significance values and effect‑size estimates are provided.

**Acceptance Scenarios**:

1. **Given** a completed model, **when** the researcher requests the “top‑features” report, **then** the pipeline returns a set of highest‑importance SNPs and metabolites, each with p‑values (BH‑adjusted) and effect‑size coefficients.  

---

### User Story 3 – Independent Validation (Priority: P3)

A researcher wishes to evaluate the trained model on a separate public dataset that was not used during training to test generalizability.

**Why this priority**: External validation guards against over‑fitting and demonstrates that findings are not dataset‑specific.

**Independent Test**: Provide a second public dataset to the pipeline’s validation mode and verify that performance metrics are computed and reported.

**Acceptance Scenarios**:

1. **Given** a trained model and an independent paired genotype‑metabolite‑phenotype dataset, **when** the validation step runs, **then** it outputs the same performance metrics (accuracy / AUC‑ROC / R²) and confirms whether the ≥ 75 % target is maintained.

---

### Edge Cases

- What happens when a selected public dataset lacks either genomic or metabolomic measurements for some samples?  
- How does the system handle a phenotype column that is missing, malformed, or recorded in an unexpected scale?  
- What if the number of available matched samples is below the minimum required for reliable cross‑validation (e.g., < 30 samples)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve paired genomic (SNP) and metabolomic datasets for a given plant species from public repositories, ensuring each sample includes genotype, metabolite profile, and resistance phenotype. (See US‑1)  
- **FR-002**: System MUST preprocess raw sequencing reads with `fastp` and call variants with `bcftools` to generate a SNP matrix, and must normalize metabolomics data using a MetaboAnalyst‑compatible pipeline, producing aligned feature tables ready for joint analysis. (See US‑1)  
- **FR-003**: System MUST perform feature selection using LASSO regression or Random‑Forest importance to identify the top **50 SNPs** and top **50 metabolites** associated with resistance, applying a significance threshold of **p < 0.05** after Benjamini‑Hochberg correction, and MUST run a sensitivity sweep over thresholds **{0.01, 0.05, 0.1}**, reporting how the selected feature set changes. (See US‑2)  
- **FR-004**: System MUST train an Elastic‑Net regression (for continuous resistance scores) **or** a Gradient‑Boosting classifier (for categorical resistant/susceptible labels) using **k‑fold cross‑validation (using an appropriate modest number of folds)**, and MUST report cross‑validated accuracy (or AUC‑ROC / R²) ensuring the metric meets **≥ 75 %** on validation folds. (See US‑1)  
- **FR-005**: System MUST assess model significance via **permutation testing (n = 1000)**, output a model‑level p‑value, and MUST compute collinearity diagnostics (Variance Inflation Factor) for all selected SNPs and metabolites, flagging any VIF > 5. (See US‑3)  
- **FR-006**: System MUST package the entire pipeline in a reproducible **Docker** container, document all commands, and MUST complete execution within **6 hours** on **2 CPU cores** with **≤ 7 GB RAM**. (See US‑1)  

### Key Entities *(include if feature involves data)*

- **Dataset**: Represents a public collection containing raw sequencing reads, raw metabolomics spectra, and a phenotype annotation file.  
- **Sample**: A single plant individual for which genotype, metabolite profile, and resistance phenotype are all available.  
- **FeatureTable**: Aligned matrix of SNPs (rows = samples, columns = variants) and metabolites (rows = samples, columns = features).  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cross‑validated predictive performance (accuracy for categorical, R² for continuous) **≥ 75 %** on the primary public dataset. (See US‑1)  
- **SC-002**: At least **10 SNPs** and **10 metabolites** remain significant (BH‑adjusted p < 0.05) across the entire sensitivity sweep of thresholds {0.01, 0.05, 0.1}. (See US‑2)  
- **SC-003**: Permutation test yields a model‑level p‑value **≤ 0.05**, confirming that observed performance exceeds chance. (See US‑3)  
- **SC-004**: End‑to‑end pipeline runtime **≤ 6 hours** and peak memory usage **≤ 7 GB** on a GitHub Actions free‑tier runner (2 CPU cores). (See US‑1)  

## Assumptions

- Public repositories contain **matched** genotype, metabolomics, and resistance phenotype data for the same set of samples.  
  - **[NEEDS CLARIFICATION: Does each selected public dataset contain matched genotype, metabolomics, and resistance phenotype for the same samples?]**  
- The resistance phenotype is recorded either as a **categorical label** (resistant / susceptible) or as a **continuous disease‑severity score**; the pipeline will auto‑detect the format.  
  - **[NEEDS CLARIFICATION: Is the resistance phenotype categorical or continuous in the available datasets?]**  
- A minimum of **100 paired samples** per dataset is assumed to provide adequate statistical power for feature selection and model training.  
  - **[NEEDS CLARIFICATION: What is the expected minimum sample size per dataset to achieve sufficient power for detecting predictive biomarkers?]**  
- Metabolomic measurements are assumed to have been generated using validated platforms (e.g., LC‑MS, GC‑MS) and can be processed with MetaboAnalyst‑compatible normalization methods.  
- All statistical analyses will be framed **associationally** (no causal claims) because the data are observational.  
- No GPU or specialized hardware is available; all computations must run on CPU‑only environments.  
- The Docker container will use only open‑source Python libraries (e.g., scikit‑learn, statsmodels, pandas) that are compatible with the free‑tier CI environment.
