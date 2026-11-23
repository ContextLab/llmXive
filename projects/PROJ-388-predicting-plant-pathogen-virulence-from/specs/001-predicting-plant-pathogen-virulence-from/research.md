# Research: Predicting Plant Pathogen Virulence from Publicly Available Genomic and Phenotypic Data

## Executive Summary
This research plan details the methodology for correlating genomic virulence factors with phenotypic disease severity in *Fusarium graminearum*, *Pseudomonas syringae*, and *Xanthomonas* spp. The approach relies on publicly available genomic data from NCBI and curated phenotypic data from PHI-base, processed through a reproducible, CPU-optimized pipeline.

## Dataset Strategy

### Verified Datasets & Source Mismatch
The "Verified datasets" block provided in the initial specification contains URLs for **human disease (NCBI Disease)** and **NLP (Winogrande/Phi)** datasets, which **do not contain** the required plant pathogen genomic or phenotypic data.
- **Gap**: No verified URL for *Fusarium*, *Pseudomonas*, or *Xanthomonas* genomes or phenotypes was provided in the "Verified datasets" block.
- **Resolution**:
  1.  **Genomes**: The pipeline will use **NCBI E-utilities** (programmatic API) to fetch real assemblies for the target taxa. This is a standard, open, programmatic method (FR-001).
  2.  **Phenotypes**: The pipeline will attempt to fetch data from the **PHI-base FTP** or **web API** (open source). If no open source is available, the plan will explicitly state "No open source found for isolate-level phenotypes" and default to **Species-level aggregation** using literature-derived averages (as per FR-009 and the "Assumptions" section of the spec).
  3.  **Compliance**: We do **not** use the dummy/irrelevant URLs provided in the "Verified datasets" block for biological analysis, as they would result in zero valid data. We document this mismatch in the "Data Availability" section.

### Data Availability & Feasibility Analysis
- **Genomes**: NCBI E-utilities provides direct, programmatic access to assemblies. No credentials required.
- **Phenotypes**: PHI-base is the primary source. Isolate-level linkage is rare.
- **Fallback**: If isolate-level linkage fails for >50% of taxa, the system falls back to **Species Aggregate** analysis. Note: Statistical testing (PGLS/Spearman) is **skipped** if N < 10 (e.g., N=3 for species level).

### Dataset-Variable Fit
- **Required Variables**: Virulence gene presence (binary), TF binding site counts (integer), Disease Severity Score (float), Phylogenetic Tree (Newick).
- **Fit**:
  - **NCBI**: Contains genomes -> Genes can be extracted.
  - **PHI-base**: Contains gene-phenotype links. *Issue*: Isolate-level linkage is rare. *Plan*: Aggregate to species level if isolate-level fails (FR-009).
  - **Phylogeny**: Constructed from **housekeeping genes** (distinct from virulence genes) to ensure independence of predictors and tree.

## Statistical Rigor

### Methodology
1.  **Correlation**:
    - **Primary (N < 30)**: **Phylogenetic Signal-Adjusted Spearman Rank Correlation**. This method accounts for phylogenetic non-independence without requiring the large sample sizes PGLS needs.
    - **Secondary (N >= 30)**: **Phylogenetic Generalized Least Squares (PGLS)**. Assumes Brownian Motion trait evolution.
    - **Robustness Check (High Dimensionality)**: **L1-regularized (Lasso) Regression** to handle p >> n scenarios.
2.  **Phylogenetic Correction**:
    - **Tree Construction**: Maximum Likelihood (ML) tree built from **housekeeping genes** (e.g., rpoB, gyrB) to avoid circularity with virulence predictors.
    - **Permutation**: **Phylogenetic Independent Contrasts (PIC) shuffling** of residuals. This preserves the tree structure while breaking the phenotype-genotype link, ensuring a valid null distribution.
3.  **Multiple Testing**:
    - **Primary**: **Benjamini-Hochberg (BH)** procedure, as mandated by Constitution Principle VI.
    - **Sensitivity**: **Benjamini-Yekutieli (BY)** used to test robustness against dependency.
    - **Acknowledgement**: Given small N and high collinearity, BH may be conservative. Raw effect sizes are reported alongside corrected p-values.
4.  **Power Analysis**:
    - **Limitation**: With N < 50, power to detect small effect sizes is low.
    - **Mitigation**: Report effect sizes (ρ) and confidence intervals. Focus on large effects (|ρ| ≥ 0.5).
5.  **Collinearity**:
    - **Issue**: Genes in the same pathway are highly correlated.
    - **Handling**: Feature pre-filtering (variance > 0.05, presence > 10%). Do not claim independent effects for correlated genes.

### Measurement Validity
- **Virulence Genes**: Defined by PHI-base/Pfam domains. Validity depends on database completeness (Assumption).
- **Phenotypic Score**: Derived from literature or aggregated. Validity depends on the consistency of scoring methods across studies.
- **Phylogeny**: Validity depends on the use of housekeeping genes for tree construction, ensuring independence from the virulence predictors.

## Compute Feasibility & GPU Strategy
- **CPU-First**:
  - `hmmsearch`: Optimized for CPU.
  - ML Tree Construction: `ete3`/`biopython` runs on CPU.
  - Lasso/Spearman: `scikit-learn` runs on CPU.
- **GPU Escape Hatch**: Not required. No deep learning models are used.
- **Memory**: Streaming genome parsing ensures RAM usage stays < 2GB.

## Constitution Compliance
- **Reproducibility**: All seeds fixed.
- **Data Hygiene**: Checksums recorded.
- **Verified Accuracy**: Citations restricted to real sources (NCBI API, PHI-base). The invalid "Verified datasets" block is explicitly bypassed.
- **Constitution Principle VI**: Adheres to Benjamini-Hochberg FDR correction.