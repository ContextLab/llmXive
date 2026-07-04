# Feature Specification: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "How do local density and global linearity in single‑cell expression manifolds determine the fidelity of cell‑type recovery by linear versus non‑linear embeddings?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I need to automatically download three specific public scRNA-seq datasets, apply standard quality control (filtering genes expressed in <5% of cells), and retain the top highly variable genes, so that I have a consistent, clean dataset ready for geometric analysis.

**Why this priority**: Without reproducible data ingestion and preprocessing, no downstream geometric metrics or embedding comparisons can be generated. This is the foundational step for the entire study.

**Independent Test**: The pipeline can be tested by running the Snakemake workflow on a single dataset and verifying that the output matrix contains a substantial number of genes and that the row/column counts match the expected post-filtering dimensions of the source GEO accession.

**Acceptance Scenarios**:

1. **Given** a valid GEO accession ID (e.g., GSE131907), **When** the download script executes, **Then** the raw count matrix is saved to disk and matches the source file size within 1%.
2. **Given** a raw count matrix, **When** the preprocessing step filters genes expressed in <5% of cells, **Then** the resulting matrix contains only genes meeting the threshold and the total cell count remains unchanged.
3. **Given** a preprocessed matrix, **When** the top 2000 highly variable genes are selected by variance ranking, **Then** the output matrix has a sufficient number of columns and the variance of selected genes is strictly higher than unselected genes.

---

### User Story 2 - Geometric Diagnostics and Embedding Generation (Priority: P2)

As a researcher, I need the system to compute global linearity (average pairwise Pearson correlation of cell embeddings) and local density (average k-NN distance with k=30 in PC space) metrics, and generate three embeddings (PCA, t-SNE, UMAP) for each dataset, so that I can quantify the data structure and prepare it for clustering.

**Why this priority**: This story delivers the core scientific variables (linearity, density) and the experimental conditions (embeddings) required to test the research hypothesis.

**Independent Test**: The system can be tested by running the diagnostics on a synthetic dataset with known geometry and verifying that the linearity score is high for a linear manifold and low for a curved one, and that the embeddings are generated without GPU errors.

**Acceptance Scenarios**:

1. **Given** a high-dimensional gene expression matrix, **When** the global linearity metric is computed on the top PCs, **Then** a single scalar value representing the average pairwise Pearson correlation of cell embeddings is output and matches the known ground truth of a synthetic linear manifold within a tolerance of ±0.01.
2. **Given** a high-dimensional matrix, **When** the local density metric is computed with k=30 in the -dimensional PC space, **Then** the average k-nearest-neighbor distance is calculated and output as a scalar.
3. **Given** a preprocessed matrix, **When** PCA, t-SNE, and UMAP are executed with specified parameters (30 PCs, perplexity=30, n_neighbors=15), **Then** three distinct 2D/3D embedding matrices are saved, each with the same number of rows as the input.

---

### User Story 3 - Fidelity Assessment and Statistical Modeling (Priority: P3)

As a researcher, I need the system to cluster the embeddings (Leiden, resolution=0.5), calculate ARI and NMI against ground-truth labels, and fit a fixed-effects linear model to test the interaction between method and geometric properties, so that I can statistically validate the hypothesis.

**Why this priority**: This story synthesizes all previous steps to produce the final scientific conclusion (the interaction effect), fulfilling the primary research question.

**Independent Test**: The system can be tested by running the full statistical model on a small subset of data and verifying that the linear model converges and outputs valid p-values for the interaction terms.

**Acceptance Scenarios**:

1. **Given** an embedding matrix and ground-truth labels, **When** Leiden clustering (resolution=0.5) is applied, **Then** a cluster assignment vector is generated for each cell.
2. **Given** cluster assignments and ground-truth labels, **When** fidelity metrics are computed, **Then** both Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI) values are output.
3. **Given** a dataset of (method, linearity, density, fidelity) tuples, **When** the fixed-effects linear model is fitted, **Then** the model outputs coefficients and p-values for the interaction terms `method:global_linearity` and `method:local_density` that are finite, non-NaN numbers.

---

### User Story 4 - CI Resource Constraint Compliance (Priority: P4)

As a CI/CD engineer, I need the analysis pipeline to complete within the GitHub Actions free-tier time limit and memory limit, so that the study can be reproduced automatically without requiring paid infrastructure.

**Why this priority**: This story ensures the research workflow is sustainable and reproducible within standard open-source constraints, preventing execution failures due to resource exhaustion.

**Independent Test**: The pipeline can be tested by running the full workflow on a GitHub Actions runner and verifying that the total runtime is < 6 hours and peak RAM usage is < 7GB.

**Acceptance Scenarios**:

1. **Given** the full Snakemake workflow, **When** executed on a GitHub Actions free-tier runner, **Then** the process completes successfully without a timeout error.
2. **Given** the full Snakemake workflow, **When** executed on a GitHub Actions free-tier runner, **Then** the peak RAM usage recorded does not exceed a moderate threshold.

---

### Edge Cases

- What happens when a dataset has a number of genes below a sufficient threshold after filtering? The system must flag the dataset as insufficient and skip it, logging a warning rather than crashing.
- How does the system handle a dataset where the ground-truth labels are missing or malformed? The system must abort processing for that specific accession and log the error to the report without halting the entire pipeline.
- What happens if the linear model fails to converge due to collinearity? The system must catch the convergence error, attempt a simplified model (removing interaction terms), and record the failure in the report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download raw count matrices from GEO for at least three valid accessions defined in a configuration file (e.g., GSE*, GSE150728, GSE176078) using `wget` or `GEOquery`. (See US-1)
- **FR-002**: System MUST filter genes expressed in <5% of cells and retain a subset of highly variable genes by variance ranking for all downstream steps. (See US-1)
- **FR-003**: System MUST compute a global linearity score defined as the average pairwise Pearson correlation of cell embeddings (top principal components). (See US-2)
- **FR-004**: System MUST compute a local density estimate defined as the average k-nearest-neighbor distance with k=30 on the 30-dimensional PC space. (See US-2)
- **FR-005**: System MUST generate three embeddings per dataset: PCA (principal component analysis)

The research question is to identify the dominant patterns of variation in the dataset. The method involves applying principal component analysis to reduce dimensionality and extract the most significant components. References: [Insert specific DOI/arXiv/author-year here]., t-SNE (perplexity=30, A sufficient number of iterations will be performed to ensure convergence and stability of the results.), and UMAP (n_neighbors=15, min_dist=0.1). (See US-2)
- **FR-006**: System MUST apply Leiden clustering with resolution=0.5 to each embedding to generate cluster assignments. (See US-3)
- **FR-007**: System MUST calculate Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI) between Leiden clusters and ground-truth labels. (See US-3)
- **FR-008**: System MUST fit a fixed-effects linear model: `fidelity ~ method + global_linearity + local_density + method:global_linearity + method:local_density + dataset`. (See US-3)
- **FR-009**: System MUST perform F-tests (ANOVA) on interaction terms with α=0.05 to determine statistical significance. (See US-3)
- **FR-010**: System MUST record wall-clock time and peak RAM for each embedding step using `/usr/bin/time -v` to verify CPU-only feasibility. (See US-3)

### Key Entities

- **Dataset**: A collection of gene expression counts associated with a specific GEO accession, containing cells as rows and genes as columns.
- **Embedding**: A low-dimensional representation (2D or 3D) of the high-dimensional data generated by PCA, t-SNE, or UMAP.
- **Geometric Metric**: A scalar value representing either global linearity or local density derived from the principal component space.
- **Fidelity Score**: A scalar value (ARI or NMI) representing the agreement between clustering results and ground-truth cell-type labels.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The statistical significance (p-value < 0.05) of the interaction between `method` and `global_linearity` is measured against the null hypothesis of no interaction, using F-tests (ANOVA) on the fixed-effects model output. (See US-3)
- **SC-002**: The statistical significance (p-value < 0.05) of the interaction between `method` and `local_density` is measured against the null hypothesis of no interaction, using F-tests (ANOVA) on the fixed-effects model output. (See US-3)
- **SC-003**: The peak RAM usage for the most memory-intensive embedding step (t-SNE or UMAP) is measured against the available memory limit of the GitHub Actions free-tier runner. (See US-4)
- **SC-004**: The total wall-clock time for the complete pipeline (download to report generation) is measured against the free-tier runner time limit of GitHub Actions. (See US-4)
- **SC-005**: The reproducibility of the results is measured by the successful execution of the Snakemake workflow on a clean environment with pinned versions in `environment.yml`. (See US-3)

## Assumptions

- The three selected GEO datasets (GSE, GSE150728, GSE176078) contain valid ground-truth cell-type annotations in their metadata.
- The `scikit-learn`, `umap-learn`, and `leidenalg` Python packages can be installed and run on a CPU-only environment without requiring CUDA or GPU acceleration.
- The "global linearity" metric (average pairwise Pearson correlation of cell embeddings) is a valid proxy for the curvature of the data manifold in the context of scRNA-seq data.
- The "local density" metric (average k-NN distance with k=30 in PC space) is a valid proxy for the heterogeneity of local density in the data manifold.
- The Leiden algorithm with resolution=0.5 provides a reasonable baseline clustering for evaluating embedding fidelity across diverse datasets.
- The sample size (number of datasets, n=3) is sufficient to demonstrate the statistical interaction using a fixed-effects model, acknowledging that this is a pilot study with limited power.
- The `GEOquery` R package or equivalent Python tools are available and functional within the CI environment for data retrieval.
- The ground-truth labels provided in GEO metadata are accurate and can be used as the reference standard for ARI/NMI calculation.
- The `Snakemake` workflow engine is available in the CI environment or can be installed via `pip` without exceeding the 6-hour runtime limit.