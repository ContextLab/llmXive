# Feature Specification: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data"

## User Scenarios & Testing

### User Story 1 - Compute Geometric Diagnostics and Generate Embeddings (Priority: P1)

The system must ingest raw scRNA-seq count matrices, preprocess them (log-CPM, gene filtering), and compute two specific geometric descriptors (global linearity, local continuity) on the high-dimensional space. Simultaneously, it must generate three distinct low-dimensional embeddings (PCA, t-SNE, UMAP) using fixed, reproducible hyperparameters.

**Why this priority**: This is the foundational data transformation step. Without accurate geometric diagnostics and embeddings, no fidelity assessment or statistical modeling can occur. It delivers the primary data artifacts required for the research question.

**Independent Test**: The pipeline can be run on a single dataset; the output includes a JSON file with linearity/density scores and three embedding matrices (CSV/Parquet) which can be manually inspected for shape and non-null values.

**Acceptance Scenarios**:

1. **Given** a raw GEO count matrix with >10,000 cells and >20,000 genes, **When** the preprocessing step runs, **Then** the output contains the top N highly variable genes, where N is determined by the variance-stabilizing selection method, and a log-CPM transformed matrix.
2. **Given** the preprocessed matrix, **When** geometric diagnostics are computed, **Then** the system outputs a global linearity score (Trustworthiness metric) and a local continuity score (Local Continuity metric) as numeric floats.
3. **Given** the preprocessed matrix, **When** embeddings are generated, **Then** the system produces three distinct 2D/3D coordinate sets (PCA, t-SNE, UMAP) with dimensions matching the input cell count.

---

### User Story 2 - Quantify Cell-Type Recovery Fidelity (Priority: P2)

The system must perform unsupervised clustering (Leiden algorithm) on each generated embedding. For each embedding, it must determine the optimal number of clusters by maximizing the Silhouette Score, then compute the Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI) against the ground-truth biological labels provided in the metadata.

**Why this priority**: This step translates the geometric transformations into a measurable performance metric (fidelity). It directly addresses the "outcome variable" of the research question.

**Independent Test**: The system can be run on a dataset with known labels; the output includes a table mapping each method to its ARI and NMI scores, which can be validated against manual calculations on a small subset.

**Acceptance Scenarios**:

1. **Given** a PCA embedding and ground-truth cell-type labels, **When** the Leiden clustering (resolution optimized by Silhouette Score) runs, **Then** the system computes an ARI score between 0.0 and 1.0.
2. **Given** a t-SNE embedding and ground-truth labels, **When** the Leiden clustering (resolution optimized by Silhouette Score) runs, **Then** the system computes an NMI score between 0.0 and 1.0.
3. **Given** multiple datasets, **When** fidelity metrics are aggregated, **Then** the system produces a summary table where every dataset-method combination has a valid ARI and NMI value (no nulls).

---

### User Story 3 - Execute Statistical Interaction Analysis and Sensitivity Sweep (Priority: P3)

The system must fit a mixed-effects model to test the effect of method type on fidelity, accounting for dataset variability. Crucially, it must perform a sensitivity analysis on the clustering optimization metric (sweeping Silhouette thresholds) to ensure robustness, and apply multiple-comparison corrections.

**Why this priority**: This delivers the statistical conclusion and ensures methodological soundness (addressing multiplicity and threshold justification). It is the final analytical step required to answer the research question.

**Independent Test**: The system outputs a statistical report containing p-values for method effects and a sensitivity plot showing how ARI/NMI varies with clustering optimization; the p-values must be adjusted for multiple testing.

**Acceptance Scenarios**:

1. **Given** the fidelity metrics and geometric scores, **When** the mixed-effects model runs, **Then** the output includes a likelihood-ratio test p-value for the `method` fixed effect.
2. **Given** the primary clustering optimization (Silhouette maximization), **When** the sensitivity sweep runs, **Then** the system recalculates ARI/NMI for Silhouette thresholds {0.4, 0.5, 0.6} and reports the variance in headline rates.
3. **Given** multiple hypothesis tests (e.g., testing multiple method comparisons), **When** the analysis completes, **Then** the reported p-values are corrected using the Benjamini-Hochberg procedure (FDR < 0.05).

### Edge Cases

- What happens when a dataset has extremely low cell counts (<500), causing k-nearest neighbor distance calculations to be unstable? The system must log a warning and skip geometric diagnostics for that dataset.
- How does the system handle a dataset where the ground-truth labels are missing or incomplete? The system must abort the fidelity calculation for that specific dataset and report the error in the final summary.
- What if the Leiden algorithm fails to converge within the iteration limit for a specific embedding? The system must retry with a fixed random seed; if it fails twice, it marks the result as "Unavailable" rather than crashing the pipeline.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess at least three public scRNA-seq datasets (specifically: GSE, GSE, GSE) using log-CPM transformation and retaining the top N highly variable genes, where N is determined by the variance-stabilizing selection method (See US-1).
- **FR-002**: System MUST compute a global linearity score defined as the Trustworthiness metric (k=15) on the high-dimensional space, calculated [deferred] randomly sampled cell pairs to ensure computational feasibility (See US-1).
- **FR-003**: System MUST compute a local continuity estimate defined as the Local Continuity (LCA) metric (k=15) on the high-dimensional space (See US-1).
- **FR-004**: System MUST generate three embeddings per dataset: PCA (top principal components), t-SNE (perplexity=30, 1000 iterations), and UMAP (n_neighbors=15, min_dist=0.1) (See US-1).
- **FR-005**: System MUST calculate Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI) between Leiden clusters (where the number of clusters is optimized to maximize the Silhouette Score) and ground-truth labels for every embedding (See US-2).
- **FR-006**: System MUST fit a mixed-effects model with the formula `fidelity ~ method + (1|dataset)` to test the fixed effect of the dimensionality reduction method on fidelity, with dataset as a random intercept (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis by sweeping the Silhouette Score optimization threshold over the set {0.4, 0.5, 0.6} and reporting the variance in ARI/NMI (See US-3).
- **FR-008**: System MUST apply Benjamini-Hochberg correction to all p-values derived from multiple hypothesis tests to control the False Discovery Rate (See US-3).

### Key Entities

- **Dataset**: A collection of raw gene expression counts, associated metadata (cell-type labels), and computed geometric properties.
- **Embedding**: A low-dimensional representation (matrix of coordinates) of the cells derived from a specific algorithm (PCA, t-SNE, UMAP).
- **FidelityMetric**: A scalar value (ARI or NMI) quantifying the agreement between clustering results and ground-truth labels.
- **GeometricDescriptor**: A scalar value representing either global linearity (Trustworthiness) or local continuity (LCA) of the high-dimensional manifold.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance in ARI/NMI across the sensitivity sweep (Silhouette thresholds {0.4, 0.5, 0.6}) is measured against the stability threshold (variance < 0.05) to confirm the primary result is not an artifact of a single arbitrary cutoff (See FR-007, US-3).
- **SC-002**: The interaction p-value (method effect) is measured against the significance level α=0.05 (after FDR correction) to determine if the method significantly predicts fidelity (See FR-008, US-3).
- **SC-003**: The peak memory usage of the entire pipeline is measured against the GitHub Actions runner RAM limit.. Verification requires the pipeline to log peak Resident Set Size (RSS) via `/proc/self/status` or a resource-monitoring wrapper at the end of execution. The pass/fail assertion logic is: if logged peak RSS > 7,000,000,000 bytes, the test fails and the pipeline exits with code 1; otherwise, it passes (See FR-001, US-1).
- **SC-004**: The total wall-clock time of the analysis is measured against the job limit. Verification requires the pipeline to record the total CI job duration (from the start of the first step to the completion of the last step) via the CI runner's built-in timing logs or a wrapper script. The pass/fail assertion logic is: if total duration > 21,600 seconds, the test fails; otherwise, it passes (See FR-001, US-1).
- **SC-005**: The collinearity diagnostic (Variance Inflation Factor) for predictors is measured against the threshold VIF < 5; the study proceeds only if VIF < 5 for all predictors, otherwise the analysis is flagged as collinear and the model is aborted (See US-3).

## Assumptions

- The three selected GEO datasets (GSE131907, GSE111322, GSE150728) contain sufficient cell counts (>1,000) and high-quality ground-truth cell-type annotations to support statistical modeling.
- The `scikit-learn` and `umap-learn` libraries can execute the specified hyperparameters (e.g., t-SNE perplexity=30) on a CPU-only environment within the 6-hour time limit without GPU acceleration.
- The ground-truth cell-type labels in the GEO metadata are accurate and consistent with the biological definitions used in the clustering evaluation.
- The global linearity metric (Trustworthiness) and local continuity metric (LCA) are computationally feasible on the high-dimensional space (with [deferred] random pair sampling) without requiring dimensionality reduction prior to calculation.
- The Benjamini-Hochberg correction is the appropriate method for controlling false discoveries given the small number of hypothesis tests (method comparisons) being performed.
- The sensitivity analysis sweep of Silhouette thresholds across a representative range is sufficient to capture the stability of the clustering results; wider sweeps are deferred to future work.
- The mixed-effects model assumptions (normality of residuals, homoscedasticity) are approximately met by the fidelity metrics after transformation if necessary.