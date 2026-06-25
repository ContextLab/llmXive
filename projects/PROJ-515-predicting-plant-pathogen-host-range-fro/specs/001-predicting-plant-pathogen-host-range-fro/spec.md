# Feature Specification: Predicting Plant Pathogen Host Range from Publicly Available Genomic and Interaction Data

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “Develop a computational pipeline that extracts genomic features from publicly available plant‑pathogen genomes, integrates these with host‑pathogen interaction records, and builds an interpretable logistic‑regression model to predict infection likelihood and identify genomic determinants of host‑range breadth.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Generate Predictive Host‑Range Model (Priority: P1)

A researcher wants to run the pipeline on a curated set of plant pathogens and obtain a cross‑validated logistic‑regression model that predicts whether a pathogen can infect a given plant species.

**Why this priority**: This is the core scientific deliverable; without a working model the project cannot answer the primary research question.

**Independent Test**: Execute the pipeline on a test subset of 10 pathogens (≤ 5 GB total data) and verify that a model object is saved, cross‑validation AUPRC is reported, and the model file can be loaded without error.

**Acceptance Scenarios**:

1. **Given** a directory containing 10 pathogen genome FASTA files and a matching interaction CSV, **when** the user runs `run_pipeline.sh --data-dir ./test_data`, **then** a `model.pkl` file is produced and the console prints “Cross‑validated AUPRC = 0.73 (±0.04)”.
2. **Given** the same inputs, **when** the user inspects `feature_importance.csv`, **then** at least three genomic feature categories have non‑zero SHAP importance values.

---

### User Story 2 – Identify Significant Genomic Feature Categories (Priority: P2)

A plant‑pathology specialist wants to know which genomic feature groups (e.g., effector counts, secondary‑metabolism clusters) are statistically associated with broad host ranges.

**Why this priority**: The scientific insight (feature identification) is the secondary but essential outcome; it guides downstream breeding or biosecurity decisions.

**Independent Test**: Run the pipeline on the full multi‑pathogen dataset and verify that a report `significant_features.tsv` lists feature categories passing permutation‑test significance (α = 0.05) after multiple‑comparison correction.

**Acceptance Scenarios**:

1. **Given** the full dataset, **when** the pipeline finishes, **then** `significant_features.tsv` contains ≥ 2 rows and each row includes the feature name, effect size (Cohen’s d), and adjusted p‑value ≤ 0.05.

---

### User Story 3 – Predict Host‑Range for a Novel Pathogen (Priority: P3)

A biosecurity analyst discovers a newly sequenced fungal pathogen and wants a quick prediction of its potential plant hosts.

**Why this priority**: Real‑world applicability; demonstrates that the model can be used on unseen data, supporting rapid risk assessment.

**Independent Test**: Provide a single novel genome FASTA and run `predict_host_range.sh --genome novel.fa`. Verify that a CSV `prediction.csv` is output with probability scores for each plant species in the interaction reference.

**Acceptance Scenarios**:

1. **Given** a novel genome file, **when** the prediction script is executed, **then** `prediction.csv` lists ≥ 20 plant species with probability values between 0 and 1, and the top‑5 predictions have probabilities ≥ 0.60.

---

### Edge Cases

- **Missing Genome**: If a pathogen listed in the interaction matrix lacks a corresponding genome file, the pipeline should log a warning and skip that pathogen without aborting.
- **Incomplete Interaction Record**: When a host‑pathogen pair has ambiguous or duplicate entries, the pipeline must deduplicate based on unique (pathogen, host) keys and proceed.
- **Zero‑Feature Pathogen**: If a pathogen’s computed feature vector is all zeros (e.g., no effectors detected), the model should assign a baseline probability equal to the overall prevalence of infection in the training data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download pathogen genome FASTA files from NCBI GenBank given a list of accession numbers.
- **FR-002**: The system MUST parse publicly available host‑pathogen interaction tables (PHI‑base, Interactome3D, or NCBI BioSample) and construct a binary interaction matrix (pathogen × host).
- **FR-003**: The system MUST compute the following genomic feature vectors for each pathogen:  
  a) Effector protein count (using a curated effector HMM library).  
  b) Gene‑family abundance (Pfam domain counts).  
  c) GC content (percentage).  
  d) 4‑mer frequency profile (normalized counts).  
- **FR-004**: The system MUST train a regularized logistic‑regression classifier (L2 penalty, λ determined by inner 5‑fold CV) to predict infection (binary) from the feature vectors.
- **FR-005**: The system MUST evaluate model performance using 5‑fold cross‑validation and report AUPRC, precision at [deferred] recall, and calibrated probability scores.
- **FR-006**: The system MUST conduct permutation testing (1 000 permutations, α = 0.05) with Benjamini‑Hochberg FDR correction to assess feature‑importance significance.
- **FR-007**: The system MUST generate SHAP value files for all features and produce a ranked list of significant feature categories.
- **FR-008**: The system MUST run entirely on CPU‑only hardware, using only libraries that do not require CUDA or GPU acceleration (e.g., scikit‑learn, pandas, numpy, shap‑cpu).
- **FR-009**: The system MUST enforce a maximum memory footprint of several GB and a total runtime ≤ 5 hours on a GitHub Actions free‑tier runner for the full 50‑pathogen dataset.
- **FR-010**: The system MUST log all processing steps to a `pipeline.log` file with timestamps and error levels.

*Clarification markers*:

- **FR-003**: [NEEDS CLARIFICATION: Does PHI‑base provide a comprehensive list of host species for each pathogen, or are supplemental sources required to capture full host‑range breadth?]  
- **FR-006**: [NEEDS CLARIFICATION: Are there any pre‑published effect‑size thresholds for feature importance that should be used in addition to the α = 0.05 cutoff?]  

### Key Entities

- **Pathogen**: Represents a plant‑pathogenic organism; key attributes include `accession_id`, `taxonomic_group`, `genome_path`.
- **Host**: Represents a plant species; key attributes include `species_name`, `taxonomic_id`.
- **InteractionRecord**: Binary relation (`pathogen_id`, `host_id`, `infects` ∈ {0,1}).
- **FeatureVector**: Numeric vector of the four genomic feature categories for a given pathogen.
- **ModelArtifact**: Serialized logistic‑regression model (`model.pkl`) together with scaler parameters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cross‑validated AUPRC of the logistic‑regression model on the full dataset must be ≥ 0.70 and at least 0.05 points higher than a random‑baseline predictor (p < 0.01, two‑tailed paired t‑test).
- **SC-002**: At least two genomic feature categories must achieve statistically significant importance after FDR correction (adjusted p ≤ 0.05) and exhibit effect sizes (Cohen’s d) ≥ 0.4.
- **SC-003**: Prediction runtime for a single novel pathogen genome (≤ 100 Mb) must be ≤ 30 seconds on a 2‑core CPU runner, and memory usage must stay below an acceptable upper limit..
- **SC-004**: The pipeline must complete end‑to‑end on the full 50‑pathogen dataset within 5 hours on the free‑tier CI environment, with total disk usage ≤ 10 GB.
- **SC-005**: All logs must contain no uncaught exceptions; the `pipeline.log` file must record at least one INFO entry for each major step (download, feature extraction, model training, evaluation, reporting).

## Assumptions

- The NCBI GenBank entries for the selected pathogens contain complete, high‑quality genome assemblies (no fragmented drafts).
- Public interaction databases (PHI‑base, Interactome3D, NCBI BioSample) collectively capture the true host‑range breadth for the chosen pathogens; any missing host records are assumed to be false negatives and do not invalidate the associative analysis.
- The genomic features specified (effector counts, Pfam domain abundances, GC content, k‑mer frequencies) are valid, independently measured variables; collinearity will be diagnosed (variance inflation factor < 5) before model fitting, and any highly collinear features will be merged or removed.
- The study is observational; therefore, all inferences are framed as **associational** (e.g., “feature X is associated with broader host range”) rather than causal.
- Multiple hypothesis testing (feature importance across four feature groups) will be controlled using Benjamini‑Hochberg FDR at α = 0.05.
- Sample‑size and statistical power considerations are acknowledged but exact power calculations are deferred to the implementation phase (`[deferred]`), with the understanding that ≥ 50 pathogens provide moderate power for detecting medium‑effect sizes.
- All software dependencies are available from PyPI and are compatible with Python 3.11 on Linux runners; no proprietary or GPU‑only packages will be used.
- Researchers using the pipeline have stable internet connectivity to download genome data and interaction tables.
