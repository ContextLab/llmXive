# Research: Predicting Coral Resilience to Thermal Stress

## 1. Dataset Strategy

The project relies on the NCBI BioProject PRJNA292777 for *Acropora millepora* genomic data.

| Dataset Component | Source / Loader | Verified URL | Status / Notes |
| :--- | :--- | :--- | :--- |
| **Genomic Variants (VCF)** | NCBI SRA/Genome | **NO verified source found** | The spec cites PRJNA292777. The `# Verified datasets` block explicitly states "NO verified source found" for PRJNA292777, VCF, and BioProject. The implementation MUST handle the scenario where the raw data cannot be programmatically fetched from a verified URL. The pipeline will be designed to accept a local file path for the VCF if the download fails or the source is unreachable. |
| **Phenotype Metadata** | NCBI BioProject | **NO verified source found** | **CRITICAL**: PRJNA is a population-level WGS study. It does **NOT** contain individual-level binary survival labels. The pipeline will attempt to derive a population-level proxy (e.g., mean thermal tolerance per population) from associated metadata or halt with a specific error if no valid proxy exists. Individual-level GWAS is infeasible with this data. |
| **Pathway Reference** | g:Profiler / Homolog DB | N/A | No specific URL provided in verified block. The implementation will use standard libraries (e.g., `gprofiler-official` if available via pip, or a local mapping file) to map genes to pathways. Cross-referencing with *Nematostella vectensis* is required (FR-008). |

**Critical Note on Data Availability**: The `# Verified datasets` block indicates that the primary data source (PRJNA292777) has **NO verified source found** and lacks the required individual-level phenotype. This is a critical risk. The plan assumes the `data/ingest.py` module will attempt to fetch from the canonical NCBI URL but must gracefully handle failure by requiring the user to provide the raw VCF/Metadata files locally. The pipeline cannot proceed without these files or a valid population-level proxy.

## 2. Statistical Methodology

### 2.1 Quality Control (QC)
- **Filtering**: Variants with MAF ≤ 0.05 or missingness > 10% will be excluded (FR-002).
- **Individual QC**: Individuals with missing genotype calls > 10% will be excluded (Edge Case).
- **Implementation**: `plink2 --maf 0.05 --geno 0.1 --mind 0.1`.

### 2.2 Population Stratification
- **Method**: Principal Component Analysis (PCA) on the filtered genotype matrix.
- **Covariates**: Top 3 Principal Components (PCs) will be extracted and included as covariates in the GWAS model (FR-009, SC-005).
- **Validation**: Genomic inflation factor (Lambda) will be calculated. **However, Lambda ≤ 1.05 is NOT a definitive pass/fail gate for small, non-natural populations.** The plan mandates **QQ-plot inspection** and, if sample size permits, **LD-score regression**. For small sample sizes, **permutation tests** will be used to validate stratification correction.

### 2.3 Association Testing
- **Model**: 
  - **Primary**: Linear Regression (if continuous population-level thermal tolerance metrics are available).
  - **Fallback**: Logistic Regression ONLY if individual binary labels are verified (unlikely with PRJNA292777).
- **Tool**: PLINK 2.0 (`--linear` or `--logistic`).
- **Correction**: False Discovery Rate (FDR) using the Benjamini-Hochberg procedure (FR-004).
- **Significance**: q < 0.05 (US-2, SC-003).
- **Null Result Handling**: If no SNPs meet the threshold, the system reports "No significant associations found" (FR-007).

### 2.4 Pathway Enrichment
- **Input**: List of significant SNPs (q < 0.05).
- **Mapping**: SNPs mapped to genes (using genomic coordinates).
- **Analysis**: Over-representation analysis against reference databases (e.g., KEGG, GO).
- **Cross-Species**: If *Acropora* annotations are missing, map to homologous genes in *Nematostella vectensis* or *Homo sapiens* (FR-008).
- **Null Model**: A rigorous null model will be applied to correct for cross-species mapping bias. The enrichment p-value will be adjusted for the number of mapped homologs and the baseline pathway frequency in the reference genome.
- **Conditioning**: Enrichment analysis will be conditioned on the *difference* in allele frequency between high-resilience and low-resilience populations (or individuals), not just the presence of significant hits.
- **Threshold**: Adjusted p < 0.05 (US-3).

## 3. Compute Feasibility & Constraints

- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
- **Strategy**:
  - Use `plink2` which is optimized for CPU.
  - Data will be converted to PLINK binary format (`.bed/.bim/.fam`) immediately after ingestion to reduce memory footprint during analysis.
  - No GPU-accelerated libraries (e.g., PyTorch, TensorFlow) will be used.
  - If the dataset size exceeds RAM limits during PCA, a random sample of variants (e.g., LD-pruned set) will be used for PCA calculation only, then applied to the full dataset.
- **Runtime Target**: ≤ 5 hours (SC-004).

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Data Source** | High (Pipeline cannot start) | The `ingest.py` module will check for local files if the NCBI fetch fails. The `quickstart.md` will explicitly instruct users to download the VCF manually if the automated fetch fails. |
| **Missing Survival Labels** | High (GWAS cannot run) | The pipeline will halt with a clear error message (US-1) if the binary label is absent, preventing invalid analysis. If population-level proxies are available, the analysis will pivot to population-level association. |
| **Zero Significant Hits** | Medium (Scientific outcome) | Treated as a valid result. A "Null Result" report will be generated (FR-007). |
| **Sparse Pathway Annotations** | Medium (Interpretability) | Implement homologous mapping to *Nematostella* or *Homo sapiens* and report the mapping confidence (FR-008). Apply null model correction for mapping bias. |
| **Circular Phenotype Derivation** | High (Scientific invalidity) | The pipeline will explicitly forbid using population-level survival rates as individual phenotypes. The analysis will only proceed with individual-level continuous metrics or population-level proxies. |

## 5. Decision Rationale

- **Why PLINK?** It is the industry standard for GWAS, highly optimized for CPU, and handles large datasets efficiently within memory constraints.
- **Why FDR over Bonferroni?** FDR is less conservative and more appropriate for exploratory genomic studies where some false positives are acceptable to find potential leads, while still controlling the proportion of false discoveries (US-2).
- **Why PCA?** Population stratification is a known confounder in GWAS. Including PCs as covariates is the standard method to correct for this (FR-009).
- **Why Population-Level Analysis?** The source data (PRJNA292777) lacks individual-level survival labels. Population-level association is the only scientifically valid approach with the available data.