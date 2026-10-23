# Feature Specification: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Feature Branch**: `feature/motif-rsfc`  
**Created**: 2026‑06‑27  
**Status**: Draft  
**Input**: User description: "Do specific network motif configurations in structural brain connectomes constrain individual variation in resting‑state functional connectivity patterns?" (see Idea Markdown)

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑End Data Pipeline (Priority: P1)

*As a neuroscientist, I want to automatically retrieve, preprocess, and store structural and resting‑state functional data for a cohort of subjects so that I can run downstream analyses without manual file handling.*

**Why this priority**: The entire investigation depends on a reliable, reproducible dataset. Without a stable pipeline, subsequent steps cannot be validated.

**Independent Test**: Execute the pipeline on a fresh CI runner; verify that for each of the selected subjects a binary structural connectome (Schaefer parcellation) and an rsFC matrix are saved to the designated output folder.

**Acceptance Scenarios**:

1. **Given** a list of 50 subject IDs, **When** the pipeline is invoked, **Then** the system downloads the diffusion tractography and resting‑state fMRI files, applies the Schaefer parcellation, and writes two NumPy `.npy` files per subject (`structural.npy`, `rsfc.npy`) without errors.
2. **Given** a subject whose diffusion data is missing, **When** the pipeline runs, **Then** the system logs a warning, skips the subject, and continues processing the remaining subjects.

---

### User Story 2 – Motif Quantification (Priority: P2)

*As a neuroscientist, I want to enumerate all 3‑node and 4‑node subgraphs in each structural connectome, compute z‑score prevalence against degree‑preserving null models, and store the motif profile so that I can relate it to functional metrics.*

**Why this priority**: Motif prevalence is the core predictor variable; accurate counting and normalization are essential for valid inference.

**Independent Test**: Run the motif‑counting script on a single preprocessed structural matrix; verify that a JSON file containing z‑scores for each motif type (both 3‑node and 4‑node) is produced and matches a reference output generated on the same data.

**Acceptance Scenarios**:

1. **Given** a binary structural adjacency matrix (treated as undirected), **When** the motif‑counting function executes, **Then** it returns a dictionary with z‑scores for all possible 3‑node and 4‑node motifs in undirected graphs, each computed against degree‑preserved random graphs (≥ 1000 iterations).
2. **Given** a disconnected graph (isolated nodes), **When** the function runs, **Then** it still completes without crash and reports z‑scores of zero for motifs that cannot occur.

---

### User Story 3 – Correlation & Reporting (Priority: P3)

*As a neuroscientist, I want to correlate motif prevalence scores with rsFC strength and global efficiency across subjects, apply Bonferroni correction, perform a permutation test, and automatically generate a PDF report with scatter plots, confidence intervals, power analysis results, and multicollinearity diagnostics.*

**Why this priority**: This story delivers the scientific answer to the research question and provides transparent evidence for reviewers.

**Independent Test**: Execute the analysis script on the full set of subjects; verify that a `results.pdf` is generated containing one page per motif type with a scatter plot, partial correlation coefficient, corrected p‑value, permutation‑test outcome, multicollinearity diagnostics, and a statement of significance.

**Acceptance Scenarios**:

1. **Given** motif z‑scores, rsFC strength, and global efficiency metrics for all subjects, **When** the correlation module runs, **Then** it computes partial Pearson **and** Spearman correlations controlling for structural global degree, applies Bonferroni correction across the primary tests (covering multiple motifs, metrics, and correlation types), and flags motifs with corrected p < 0.05.
2. **Given** the same input data, **When** the permutation test is performed (shuffling subject labels, 1000 permutations), **Then** the module reports an empirical p‑value for all motifs that is consistent with the analytical correction within 2× the standard error of the mean for the permutation distribution.
3. **Given** the input data, **When** the power analysis module runs, **Then** it reports the minimum detectable Pearson r for power=0.80, α = 0.05/32, and N = 50, and includes this in the report's limitations section. If fewer than 30 subjects remain after exclusions, the module recomputes power with the actual N and advises increasing cohort size or relaxing α to retain ≥ 0.80 power.
4. **Given** the motif z‑scores, **When** the multicollinearity check runs, **Then** it reports pairwise Pearson correlations among motif predictors and flags any predictor pair with |r| ≥ 0.9.

---

### Edge Cases

- **Missing Modality**: If a subject lacks either diffusion or rs‑fMRI data, the pipeline must log the omission and exclude the subject from all downstream calculations.
- **Zero‑Variance Metric**: If a motif's z‑score vector is constant across subjects (variance < 1e-6), the correlation routine must detect the situation, skip the test, and record "insufficient variance" in the report.
- **Resource Exhaustion**: If motif enumeration exceeds **300 seconds** on a standard 2‑core CPU runner, the script must abort gracefully, log a timeout warning, and suggest reducing the motif size (e.g. limit to 3‑node motifs). For testing, a deterministic trigger is provided via the CLI flag `--synthetic-nodes <N>` which generates a synthetic undirected graph with `<N>` nodes; invoking the script with `--synthetic-nodes 200` guarantees runtime > 300 s, enabling CI to verify the timeout behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR‑001**: The system MUST download diffusion tractography and resting‑state fMRI files for a provided list of subject IDs and store them in a reproducible directory structure. (See US‑1)
- **FR‑002**: The system MUST construct binary structural connectomes at a standard Schaefer parcellation (i.e., a chosen node resolution) using the downloaded diffusion data, treating the graph as undirected. (See US‑1)
- **FR‑003**: The system MUST compute rsFC matrices (Pearson correlation of BOLD time‑series) and derive global efficiency for each subject. (See US‑1)
- **FR‑004**: The system MUST enumerate all 3‑node **and** 4‑node subgraphs in each undirected structural connectome, generate degree‑preserving null networks (≥ 1000 iterations), **verify** that each null network preserves the original degree sequence (compare and log degree vectors), and output motif z‑score prevalence for each motif category. (See US‑2)
- **FR‑005**: The system MUST perform partial Pearson **and** Spearman correlations between each motif's z‑score and each rsFC metric (strength and global efficiency) across subjects, controlling for structural global node degree, apply Bonferroni correction for the primary tests (8 motifs × 2 metrics × 2 correlation types), and flag motifs with corrected p < 0.05. The system MUST also compute a Variance Inflation Factor (VIF) for the full set of motif predictors; if any predictor has VIF ≥ 5.0, a multicollinearity **warning** is logged, but all motifs are still tested and their p‑values reported. Additionally, the system MUST compute pairwise Pearson correlations among all motif predictors and flag any predictor pair with |r| ≥ 0.9 as a multicollinearity warning, but it MUST still report p‑values for **all** motifs. (See US‑3)
- **FR‑006**: The system MUST run a permutation test (≥ 1000 permutations, shuffling subject labels) for all tested motifs to obtain an empirical p‑value and report the result. (See US‑3)
- **FR‑007**: The system MUST generate a PDF report containing, for every tested motif, a scatter plot with a confidence interval, the partial correlation coefficient, corrected p‑value, permutation‑test outcome, and multicollinearity diagnostics (pairwise predictor correlations). (See US‑3)
- **FR‑008**: The system MUST log all processing steps, warnings, and errors to a machine‑readable `pipeline.log` file. (See US‑1)
- **FR‑009**: The system MUST include a mandatory disclaimer string in the PDF report stating: "These findings are associational only and do not imply causation." The system MUST verify the presence of this string in the generated PDF via string search. (See US‑3)
- **FR‑010**: The system MUST include a power‑analysis module that estimates the minimum detectable Pearson r given N = 50, α = 0.05 (Bonferroni‑adjusted for 32 tests), and target power = 0.80, and reports this result in a dedicated section of the PDF report, including an explicit statement of the implications for Type II error. If the effective sample size after exclusions falls below 30, the module recomputes power with the actual N and **suggests remedial actions** (e.g., increase cohort size or relax α) to retain ≥ 0.80 power. (See US‑3)
- **FR‑011**: The project MUST contain the directory hierarchy `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, `state/` with placeholder README files so that CI can verify structure existence. (See US‑1)
- **FR‑012**: The repository MUST include linting configuration files (`.flake8`, `pyproject.toml` with Black settings, and a `pre-commit` hook) and CI must enforce `flake8` and `black` compliance on all commits. (See US‑1)
- **FR‑013**: A markdown file `specs/feature/motif-rsfc/data-model.md` MUST define the data entities (Subject, StructuralConnectome, rsFCMatrix, MotifProfile) and file formats used throughout the pipeline. (See US‑2)
- **FR‑014**: The utility module `code/utils.py` MUST contain functions that validate critical runtime parameters (Bonferroni α, random seed, permutation count, VIF threshold) and ensure that all processing steps, warnings, and errors are captured in `pipeline.log`. (See US‑1)

### Data Access

The analysis will use the **Human Connectome Project (HCP) 1200‑Subject Release**. The dataset is publicly available after free registration on ConnectomeDB. Required files (minimally pre‑processed diffusion tractography and resting‑state fMRI) can be retrieved via the HCP command‑line tools:

```bash
# After registration, download a representative subset of subjects
hcp_download --project HCP1200 --modality dwi --modality rest --subjects sub-01 sub-02 ... sub-50
```

Only a limited initial subset of subjects listed in `participants.tsv` are required for this study.; the subset includes both diffusion and rs‑fMRI data, satisfying the structural‑functional pairing needed for the investigation. No manual registration of modalities is required because the HCP pipeline already aligns diffusion and functional images to a common space.

### Success Criteria *(mandatory)*

- **SC‑001**: ≥ 95 % of the 50 selected subjects have both structural and rsFC files successfully downloaded and preprocessed **without manual intervention** (i.e., no interactive prompts, exit code 0, and a complete `pipeline.log` containing only machine‑generated entries). (See US‑1)
- **SC‑002**: Motif enumeration for a single subject (3‑node **and** 4‑node, N=100 nodes, binary graph) completes in ≤ 300 seconds on a **CI runner** described as: Ubuntu 22.04, 2‑core Intel Xeon @ 2.5 GHz, Python 3.10, 8 GB RAM. (See US‑2)
- **SC‑003**: The pipeline successfully computes partial Pearson and Spearman correlations and reports Bonferroni‑corrected p‑values for all 32 primary tests; the log file contains p‑values for all motifs across both metrics and correlation types. (See US‑3)
- **SC‑004**: The PDF report is generated in ≤ 2 minutes after the last subject is processed, and the file size is ≤ 5 MB, confirming that output handling respects CI storage limits. (See US‑3)
- **SC‑005**: The power‑analysis module generates a report section containing the estimated minimum detectable Pearson r, the assumed power level (0.80), and the adjusted alpha level (α = 0.05/32). (See US‑3)
- **SC‑006**: The directory structure and linting configuration (FR‑011, FR‑012) are present and pass CI checks; the data‑model markdown (FR‑013) exists and validates against the implemented code. (See US‑1)

## Assumptions

- The HCP 1200‑Subject Release provides both diffusion tractography and minimally pre‑processed resting‑state fMRI for the same subjects; therefore no cross‑subject matching step is required.  
- Pre‑processed diffusion data are already tractographically reconstructed; the pipeline only needs to apply the Schaefer‑100 parcellation to generate binary adjacency matrices.  
- The Schaefer cortical atlas is an accepted, validated cortical parcellation for both structural and functional analyses (see Schaefer et al., 2018, DOI: 10.1016/j.neuroimage.2017.06.030).  
- All statistical computations are performed with SciPy/NumPy on the CPU; no GPU or external compute resources are required.  
- The CI environment provides ≥ 7 GB RAM and a 14 GB disk quota, sufficient for storing the 50 subjects' matrices and intermediate null‑network samples.  
- Random seeds are fixed (seed = 42) for reproducibility of null‑network generation and permutation tests.  
- The Bonferroni correction is the chosen family‑wise error control method because the number of tested hypotheses (32) is modest and the correction is computationally trivial on the CPU.  
- Motif‑z‑score significance threshold is set to |z| ≥ 2.0, a standard cutoff in network‑motif literature; a sensitivity analysis will sweep |z| ∈ {1.5, 2.0, 2.5} and report how the number of significant motifs varies.  
- Exact enumeration of small‑node motifs in a medium‑sized graph is computationally intensive; therefore, the investigation is scoped to 3‑node and 4‑node motifs only for this iteration.  
- The structural connectome is treated as an undirected binary graph for motif enumeration and null model generation, consistent with standard practices for 3‑node and 4‑node motif analysis in this context.  
- The degree‑preserving null model (Maslov‑Sneppen) is sufficient to isolate motif‑specific effects because it is the community‑standard baseline for network motif analysis, as cited in standard literature (e.g., Milo et al.).  
- The research question is framed as investigating "association" rather than "constraint" to avoid causal claims that cannot be supported by observational data.  
- Access to the HCP dataset requires registration but no additional credentials beyond the free ConnectomeDB account, satisfying CI‑platform constraints.  
- If the effective sample size after exclusions drops below 30, the power‑analysis module will recompute power with the actual N and suggest increasing the cohort size or adjusting α to retain ≥ 0.80 power.
