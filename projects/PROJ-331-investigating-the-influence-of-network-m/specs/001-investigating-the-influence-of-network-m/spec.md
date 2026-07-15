# Feature Specification: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Feature Branch**: `feature/motif-rsfc`  
**Created**: 2026‑06‑27  
**Status**: Draft  
**Input**: User description: “Do specific network motif configurations in structural brain connectomes constrain individual variation in resting‑state functional connectivity patterns?” (see Idea Markdown)

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑End Data Pipeline (Priority: P1)

*As a neuroscientist, I want to automatically retrieve, preprocess, and store structural and resting‑state functional data for a cohort of subjects so that I can run downstream analyses without manual file handling.*

**Why this priority**: The entire investigation depends on a reliable, reproducible dataset. Without a stable pipeline, subsequent steps cannot be validated.

**Independent Test**: Execute the pipeline on a fresh CI runner; verify that for each of the selected subjects a binary structural connectome (Schaefer‑100) and an rsFC matrix are saved to the designated output folder.

**Acceptance Scenarios**:

1. **Given** a list of 50 HCP subject IDs, **When** the pipeline is invoked, **Then** the system downloads the diffusion tractography and resting‑state fMRI files, applies the Schaefer‑100 parcellation, and writes two NumPy `.npy` files per subject (`structural.npy`, `rsfc.npy`) without errors.
2. **Given** a subject whose diffusion data is missing, **When** the pipeline runs, **Then** the system logs a warning, skips the subject, and continues processing the remaining subjects.

---

### User Story 2 – Motif Quantification (Priority: P2)

*As a neuroscientist, I want to enumerate all 3‑node subgraphs in each structural connectome, compute z‑score prevalence against degree‑preserving null models, and store the motif profile so that I can relate it to functional metrics.*

**Why this priority**: Motif prevalence is the core predictor variable; accurate counting and normalization are essential for valid inference.

**Independent Test**: Run the motif‑counting script on a single preprocessed structural matrix; verify that a JSON file containing z‑scores for each motif type is produced and matches a reference output generated on the same data.

**Acceptance Scenarios**:

1. **Given** a binary structural adjacency matrix, **When** the motif‑counting function executes, **Then** it returns a dictionary with z‑scores for all possible 3‑node motifs, each computed against degree‑preserved random graphs.
2. **Given** a disconnected graph (isolated nodes), **When** the function runs, **Then** it still completes without crash and reports z‑scores of zero for motifs that cannot occur.

---

### User Story 3 – Correlation & Reporting (Priority: P3)

*As a neuroscientist, I want to correlate motif prevalence scores with rsFC strength and global efficiency across subjects, apply Bonferroni correction, perform a permutation test, and automatically generate a PDF report with scatter plots and confidence intervals.*

**Why this priority**: This story delivers the scientific answer to the research question and provides transparent evidence for reviewers.

**Independent Test**: Execute the analysis script on the full set of subjects; verify that a `results.pdf` is generated containing one page per motif type with a scatter plot, partial correlation coefficient, corrected p‑value, and a statement of significance.

**Acceptance Scenarios**:

1. **Given** motif z‑scores, rsFC strength, and global efficiency metrics for all subjects, **When** the correlation module runs, **Then** it computes partial correlations controlling for global degree, applies Bonferroni correction across all tested motifs, and flags motifs with corrected p < 0.05.
2. **Given** the same input data, **When** the permutation test is performed, **Then** the module reports an empirical p‑value that is consistent with the analytical correction within 2× the standard error of the mean for the permutation distribution.

---

### Edge Cases

- **Missing Modality**: If a subject lacks either diffusion or rs‑fMRI data, the pipeline must log the omission and exclude the subject from all downstream calculations.
- **Zero‑Variance Metric**: If a motif’s z‑score vector is constant across subjects, the correlation routine must detect the situation, skip the test, and record “insufficient variance” in the report.
- **Resource Exhaustion**: If motif enumeration exceeds 300 seconds on a 2‑core CPU, the script must abort gracefully, log a timeout warning, and suggest reducing the motif size (e.g., limit to 3‑node motifs).

## Requirements *(mandatory)*

### Functional Requirements

- **FR‑001**: The system MUST download diffusion tractography and resting‑state fMRI files for a provided list of HCP subject IDs and store them in a reproducible directory structure. (See US‑1)
- **FR‑002**: The system MUST construct binary structural connectomes at the Schaefer‑100 node parcellation using the downloaded diffusion data. (See US‑1)
- **FR‑003**: The system MUST compute rsFC matrices (Pearson correlation of BOLD time‑series) and derive global efficiency for each subject. (See US‑1)
- **FR‑004**: The system MUST enumerate all n‑node subgraphs in each structural connectome, generate degree‑preserving null networks (sufficient iterations), and output motif z‑score prevalence for every n‑node motif type. (See US‑2)
- **FR‑005**: The system MUST perform partial Pearson and Spearman correlations between each motif’s z‑score and each rsFC metric (strength and global efficiency) across subjects, controlling for global node degree, apply Bonferroni correction for the total number of motifs tested, and flag motifs with corrected p < 0.05. (See US‑3)
- **FR‑006**: The system MUST run a permutation test (≥ 1000 permutations) for each significant motif to obtain an empirical p‑value and report the result. (See US‑3)
- **FR‑007**: The system MUST generate a PDF report containing, for every tested motif, a scatter plot with a confidence interval, the partial correlation coefficient, corrected p‑value, and permutation‑test outcome. (See US‑3)
- **FR‑008**: The system MUST log all processing steps, warnings, and errors to a machine‑readable `pipeline.log` file. (See US‑1)
- **FR‑009**: The system MUST include a mandatory disclaimer string in the PDF report stating: “These findings are associational only and do not imply causation.” (See US‑3)
- **FR‑010**: The system MUST include a power‑analysis module that estimates detectable effect size given N = 50, α = 0.05 (Bonferroni‑adjusted), and reports the result in a dedicated section of the PDF report. (See US‑3)

### Success Criteria *(mandatory)*

- **SC‑001**: ≥ 95 % of the 50 selected subjects have both structural and rsFC files successfully downloaded and preprocessed without manual intervention. (See US‑1)
- **SC‑002**: Motif enumeration for a single subject (3‑node only) completes in ≤ 300 seconds on a 2‑core CPU runner, confirming compute feasibility. (See US‑2)
- **SC‑003**: The pipeline successfully computes partial correlations and reports corrected p‑values for all tested ‑node motifs, regardless of whether any association is statistically significant. (See US‑3)
- **SC‑004**: The PDF report is generated in ≤ 2 minutes after the last subject is processed, and the file size is ≤ 5 MB, confirming that output handling respects CI storage limits. (See US‑3)
- **SC‑005**: The power‑analysis module generates a report section containing the estimated minimum detectable Pearson r, the assumed power level, and the adjusted alpha level. (See US‑3, via FR‑010)

## Assumptions

- The HCP large-scale Subjects Release provides both diffusion tractography and minimally pre‑processed resting‑state fMRI for the same subjects; therefore no cross‑subject matching step is required.  
- Pre‑processed diffusion data are already tractographically reconstructed; the pipeline only needs to apply the Schaefer‑100 parcellation to generate binary adjacency matrices.  
- The Schaefer cortical atlas is an accepted, validated cortical parcellation for both structural and functional analyses (see Schaefer et al., 2018).  
- All statistical computations are performed with SciPy/NumPy on the CPU; no GPU or external compute resources are required.  
- The CI environment provides ≥ 7 GB RAM and a 14 GB disk quota, sufficient for storing the 50 subjects’ matrices and intermediate null‑network samples.  
- Random seeds are fixed (seed = 42) for reproducibility of null‑network generation and permutation tests.  
- The Bonferroni correction is the chosen family‑wise error control method because the number of tested motifs is modest and the correction is computationally trivial on the CPU.  
- Motif‑z‑score significance threshold is set to |z| ≥ 2.0, a standard cutoff in network‑motif literature; a sensitivity analysis will sweep |z| ∈ {1.5, 2.0, 2.5} and report how the number of significant motifs varies.  
- Exact enumeration of small-node motifs in a medium-sized graph is computationally intractable within the 300‑second time budget; therefore, the investigation is scoped to 3‑node motifs only for this iteration.