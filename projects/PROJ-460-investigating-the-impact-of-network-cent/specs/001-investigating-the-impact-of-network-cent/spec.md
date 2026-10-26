# Feature Specification: Investigating the Impact of Network Centrality on Resting‑State Functional Connectivity in Autism Spectrum Disorder

**Feature Branch**: `001-investigating-the-impact-of-network-cent`  
**Created**: 2025-01-10  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Resting‑State Functional Connectivity in Autism Spectrum Disorder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Data Acquisition & Preprocessing Pipeline (US‑1) – Priority: P1  

The system MUST download paired resting‑state fMRI and diffusion‑weighted MRI (dMRI) data for participants from the ABIDE I/II releases, run fMRIPrep (v23+) on the fMRI scans, and generate pre‑processed time‑series and structural adjacency matrices for each subject.

**Why this priority**: All downstream analyses (centrality computation, mediation testing) depend on high‑quality, consistently pre‑processed multimodal data.

**Independent Test**: Run the pipeline on a representative subset of 5 participants on a GitHub Actions free‑tier runner and verify that (a) cleaned fMRI NIfTI files and (b) structural connectivity CSV files are produced with the expected dimensions and contain no NaNs, and that the job finishes within the 6‑hour limit.

**Acceptance Scenarios**:

1. **Given** valid ABIDE download credentials and a list of participant IDs, **When** the preprocessing pipeline executes on a 2‑core runner, **Then** cleaned fMRI time‑series files (`sub‑<id>_func_preproc.tsv`) and structural adjacency matrices (`sub‑<id>_struct_adj.csv`) are written for every participant for which data are available, and the job exits with status 0 within the allotted runtime.  
2. **Given** a participant whose raw fMRI or dMRI file is corrupted or missing, **When** the pipeline encounters the problem, **Then** it logs a clear error, skips that participant, and continues processing the remaining subjects without aborting the whole job.

### User Story 2 – Multimodal Mediation Analysis (US‑2) – Priority: P1  

The system MUST compute (a) a global functional connectivity strength metric from the pre‑processed fMRI data, (b) the eigenvector centrality of Default Mode Network (DMN) nodes from the structural adjacency matrix, and (c) test whether the structural centrality statistically accounts for the association between functional connectivity and ADOS‑2 Social Communication scores using a bootstrap‑based mediation model. If fewer than 30 participants have paired data after quality control, the pipeline MUST abort with an explicit error.

**Why this priority**: This directly evaluates the primary scientific hypothesis about structural‑functional‑behavioral coupling in ASD.

**Independent Test**: Execute the mediation script on the full set of participants that passed US‑1 and confirm that (i) the functional metric and centrality values are written to `metrics.tsv`, (ii) a mediation model is fitted, (iii) a bootstrap distribution of thousands of resamples is saved, and (iv) the resulting indirect‑effect size, 95 % confidence interval, and bootstrap‑derived p‑value are recorded in `mediation_results.json`. All values must be derived from the actual participant data; no placeholder numbers are allowed.

**Acceptance Scenarios**:

1. **Given** ≥ 30 participants with complete fMRI, dMRI, and ADOS‑2 scores, **When** the mediation pipeline runs, **Then** `mediation_results.json` contains the indirect effect, its 95 % CI, and a p‑value, and the raw bootstrap samples are stored in `bootstrap_distribution.csv`.  
2. **Given** < 30 participants with paired data, **When** the mediation step is reached, **Then** the system writes `mediation_abort.log` with the message “Insufficient paired participants (n = X); mediation aborted.” and exits with a non‑zero status.  
3. **Given** successful execution, **When** the results are generated, **Then** `computation_manifest.txt` lists every input file (with SHA‑256 checksum), the code block that consumed it, and the output statistic produced, providing full provenance.

### User Story 3 – Sensitivity & Confounder Analysis (US‑3) – Priority: P2  

The system MUST repeat the mediation analysis across a predefined sweep of functional correlation thresholds (0.4, 0.5, 0.6, 0.7) and structural density thresholds (10 %, 20 %, 30 %), and must include age, sex, and mean framewise displacement as covariates in every model. A summary table comparing indirect‑effect sizes and p‑values across all parameter combinations must be produced.

**Why this priority**: Demonstrates that any observed mediation is robust to reasonable variations in graph‑construction choices and that confounding variables do not drive the effect.

**Independent Test**: After the primary mediation run, invoke the sensitivity driver and verify that `sensitivity_report.tsv` contains a row for each (functional threshold, structural threshold) pair with the corresponding indirect effect, CI, and p‑value. Also verify that `confounder_model_spec.txt` records the covariate inclusion syntax.

**Acceptance Scenarios**:

1. **Given** the primary mediation model completed, **When** the sensitivity sweep is launched, **Then** the system produces `sensitivity_report.tsv` with 12 rows (4 functional × 3 structural thresholds) and all required statistics.  
2. **Given** the full dataset, **When** the confounder control step executes, **Then** the mediation model includes age, sex, and mean framewise displacement as main‑effect covariates (no interaction terms) and the adjusted indirect effect is reported alongside the unadjusted one.

### Edge Cases  

- **Missing diagnosis label** – Participants lacking an ASD/TD label are excluded; the count and IDs are logged in `exclusion_log.tsv`.  
- **Excessive motion** – Participants with mean framewise displacement > 0.3 mm or any translation/rotation > 3 mm are excluded; reasons are recorded in `motion_exclusion.tsv`.  
- **Absent dMRI** – If dMRI is unavailable for a participant, that subject is omitted from structural‑centrality computation and the omission is logged in `dMRI_status.log`.  
- **Failed tractography** – When tractography yields zero streamlines for a subject, the subject is excluded from the mediation set and the failure reason is captured in `tractography_failure.tsv`.  
- **Insufficient paired participants** – Already covered in US‑2 acceptance scenario 2.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR‑001** – System MUST download resting‑state fMRI data for at least 100 ASD participants from ABIDE (See US‑1).  
- **FR‑002** – System MUST download diffusion‑weighted MRI (dMRI) for participants that have both modalities; a minimum of 30 paired participants is required for mediation (See US‑2).  
- **FR‑003** – System MUST preprocess fMRI with fMRIPrep v23+ inside a Docker container, performing slice‑time correction, motion correction, spatial normalization to MNI152, and nuisance regression (white matter, CSF, six motion parameters) (See US‑1).  
- **FR‑004** – System MUST download the Schaefer 400‑parcel atlas from the Nilearn repository, verify its SHA‑256 hash against the official value, and abort with “Atlas verification failed.” if the hash mismatches (See US‑1).  
- **FR‑005** – System MUST exclude participants whose mean framewise displacement exceeds 0.3 mm or whose translation/rotation exceeds 3 mm, logging exclusions (See US‑1, Edge Cases).  
- **FR‑006** – System MUST apply a **functional‑connectivity correlation threshold** of **0.6** as the primary pre‑registered value (justified by prior ASD network‑topology studies reporting stable graph properties around this cutoff). The threshold must be recorded in `connectivity_threshold.log`. (See US‑2).  
- **FR‑007** – System MUST pre‑register the functional threshold on OSF before any data processing; if the OSF record is not found, the pipeline aborts with “Threshold pre‑registration required.” (See US‑2).  
- **FR‑008** – System MUST compute **global functional connectivity strength** (X) as the mean absolute Fisher‑z‑transformed correlation across all edges that survive the functional threshold (See US‑2).  
- **FR‑009** – System MUST threshold the structural adjacency matrix by retaining the top **[deferred]** of streamline counts (density‑matching) and compute **eigenvector centrality** for the DMN nodes (M). The structural threshold is logged in `structural_threshold.log`. (See US‑2).
- **FR‑010** – System MUST compute the **average eigenvector centrality** across all DMN parcels for each subject (See US‑2).  
- **FR‑011** – System MUST fit a mediation model: Y = ADOS‑2 Social Communication score, X = global functional strength, M = average DMN structural centrality, covariates = age, sex, mean FD. The model must use ordinary least squares for the paths and bootstrap 5 000 resamples for the indirect effect (See US‑2).  
- **FR‑012** – System MUST abort mediation (and write `mediation_abort.log`) if < 30 paired participants remain after QC (See US‑2).  
- **FR‑013** – System MUST guarantee that **all reported statistics are derived exclusively from the processed participant data**; no simulated, hard‑coded, or placeholder values are permitted. A provenance manifest (`computation_manifest.txt`) must list each input file checksum, the code block that consumed it, and the resulting statistic (See US‑2).  
- **FR‑014** – System MUST frame all findings as **ASSOCIATIONAL** (no causal language) because the study is observational (See US‑2).  
- **FR‑015** – System MUST report the 95% confidence intervals for all model coefficients and compute the Minimum Detectable Effect Size (MDES) for the observed sample size at α=0.05 and power=0.8, reporting these in `effect_size_analysis.txt` (See US‑2).  
- **FR‑016** – System MUST conduct a sensitivity sweep over functional thresholds {0.4, 0.5, 0.6, 0.7} and structural density thresholds {10 %, 20 %, 30 %}, recompute the mediation for each combination, and output `sensitivity_report.tsv` (See US‑3).  
- **FR‑017** – System MUST include age, sex, and mean FD as main‑effect covariates in every mediation model; interaction terms are omitted (See US‑3). The covariate specification is saved in `confounder_model_spec.txt`.  
- **FR‑018** – System MUST detect disconnected graphs after thresholding; if a graph is disconnected, it must apply a minimum‑spanning‑tree augmentation **only for downstream visualization**, while centrality values are computed on the original thresholded graph (See US‑2).  
- **FR‑019** – System MUST log data‑completeness for each required variable (fMRI, dMRI, ADOS‑2, age, sex, motion) in `data_completeness_report.txt`. If any variable is missing for > 50 % of the cohort, mediation aborts with a clear error (See US‑2).  
- **FR‑020** – System MUST output the full bootstrap distribution (`bootstrap_distribution.csv`) with header `bootstrap_id,indirect_effect,direct_effect,total_effect` and exactly 5 000 rows (See US‑2).  
- **FR‑021** – To prevent fabricated results, the system MUST generate a `computation_audit.log` recording the raw summary statistics (mean, std, n) for all variables used in the mediation model immediately prior to fitting (See US‑2).  
- **FR‑022** – System MUST capture the reason for tractography failure (e.g., zero streamlines) and log it in `tractography_failure.tsv` (See US‑1).  
- **FR‑023** – System MUST generate a path diagram illustrating the direct, indirect, and total effects of the mediation model using the bootstrap-derived coefficients (See US‑2).  
- **FR‑024** – System MUST overlay the DMN hub locations (nodes with highest eigenvector centrality) on a standard MNI152 brain template using Nilearn for visualization (See US‑2).  

*All functional requirements reference the corresponding user story in parentheses (e.g., (See US‑1)).*

### Key Entities *(include if feature involves data)*

- **Participant** – Subject identifier with attributes: age, sex, diagnosis, mean framewise displacement, ADOS‑2 Social Communication score, fMRI time‑series, dMRI streamline matrix.  
- **FuncTimeSeries** – Preprocessed fMRI signal matrix (timepoints × 400 parcels).  
- **FuncAdjacency** – Binary/weighted functional connectivity matrix after applying the functional correlation threshold.  
- **StructAdjacency** – Weighted structural connectivity matrix derived from dMRI tractography, thresholded by density.  
- **DMNCentrality** – Eigenvector centrality values for the set of DMN parcels extracted from `StructAdjacency`.  
- **MediationResult** – JSON object containing direct effect, indirect effect, total effect, 95 % CI, p‑value, and bootstrap metadata for each (functional threshold, structural threshold) pair.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC‑001** – ≥ 90 % of downloaded participants produce valid preprocessed fMRI time‑series files (no NaNs, correct dimensions) (See US‑1).  
- **SC‑002** – ≥ 95 % of participants with paired data have non‑null eigenvector centrality values within the normalized range [0, 1] (See US‑2).  
- **SC‑003** – The mediation analysis outputs a bootstrap‑derived 95 % confidence interval and p‑value for the indirect effect; the raw bootstrap distribution (`bootstrap_distribution.csv`) must contain exactly 5 000 rows (See FR‑020, US‑2).  
- **SC‑004** – The sensitivity report (`sensitivity_report.tsv`) contains indirect‑effect estimates for all 12 (functional × structural) threshold combinations (See FR‑016, US‑3).  
- **SC‑005** – The confounder‑controlled model includes age, sex, and mean FD as covariates and reports the adjusted indirect effect (See FR‑017, US‑3).  
- **SC‑006** – `data_availability_report.txt` and `data_completeness_report.txt` are generated and contain entries for ≥ 95 % of participants (See FR‑019).  
- **SC‑007** – `effect_size_analysis.txt` reports numeric MDES values and 95% CIs for all mediation paths (See FR‑015).  
- **SC‑008** – All output files (`mediation_results.json`, `bootstrap_distribution.csv`, `computation_manifest.txt`, etc.) are reproducibly generated on a GitHub Actions free‑tier runner within the 6‑hour wall‑time limit (See Assumptions).  
- **SC‑009** – The `computation_manifest.txt` is programmatically verified to link every output value in `mediation_results.json` to its source input file checksums (See FR‑013, US‑2).  

## Assumptions

- The ABIDE I/II releases contain, for a sufficient subset of participants, (i) resting‑state fMRI, (ii) diffusion‑weighted MRI, (iii) ADOS‑2 Social Communication scores, (iv) age, (v) sex, and (vi) motion parameters.  
- At least 30 participants will have complete paired modalities after QC; this is the hard minimum for mediation (FR‑012).  
- fMRIPrep Docker image runs on a CPU‑only GitHub Actions runner (no GPU required).  
- The Schaefer 400‑parcel atlas is publicly available and its SHA‑256 checksum is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (example placeholder – actual checksum to be verified at implementation).  
- The functional correlation threshold of 0.6 is justified by prior ASD network‑topology literature reporting stable small‑world properties around this value (e.g., Barttfeld et al., 2012).  
- The structural density threshold of 20 % is a community‑standard compromise that balances sparsity with preservation of hub structure (see *Assumptions*).  
- The study is observational; therefore all conclusions are presented as associational, not causal (FR‑014).  
- Multiple‑comparison correction (False Discovery Rate) will be applied when reporting node‑wise centrality statistics, although the primary mediation test is a single indirect‑effect estimate.  
- All computations (graph metrics, regression, bootstrapping) are tractable on a 2‑CPU, ~7 GB RAM GitHub Actions runner and will complete within the 6‑hour job limit.  
- Clinical severity scores (ADOS‑2) are available for the majority of ASD participants; if fewer than 30 participants have ADOS‑2 scores, the mediation result will be labeled exploratory with appropriate caveats.  