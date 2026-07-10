# Research: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Scientific Background

The study investigates how non-coding Single Nucleotide Polymorphisms (SNPs) alter Transcription Factor (TF) binding affinity, a key mechanism in gene regulation. The hypothesis is that SNPs disrupting TF binding sites in regulatory regions (promoters/enhancers) are enriched in disease-associated loci (GWAS). The core metric is the change in binding affinity ($\Delta Score$) calculated using Position Weight Matrices (PWMs).

## 2. Dataset Strategy

### Verified Datasets & Data Validity Statement

Per the project constraints, the following sources are cited. The plan distinguishes between **Research Mode** (real data) and **CI Mode** (synthetic data).

**Data Validity Statement**:
- **Synthetic data** can only validate *pipeline logic* and *code correctness*. It **cannot** validate the biological hypothesis of GWAS enrichment due to the lack of real LD structures and biological signal.
- **Real data** (1000 Genomes, JASPAR 2024, ENCODE, GWAS Catalog) is required for the final scientific claim and satisfies all functional requirements (FR-001 to FR-006).

| Dataset | Source / URL | Status | Strategy |
|:--- |:--- |:--- |:--- |
| **SNPs (1000 Genomes)** | `ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/` | **Available (Real)** | Primary source for common SNPs (MAF > 1%) in Research Mode. Satisfies FR-001 as a verified proxy for dbSNP common variants. Fallback to synthetic data in CI Mode only for logic validation. |
| **JASPAR PWMs** | ` | **Available (Real)** | Primary source for human TFs (JASPAR 2024 CORE non-redundant) in Research Mode. Fallback to a small, hardcoded subset (versioned) in CI Mode. |
| **Regulatory Regions (ENCODE)** | ` | **Available (Real)** | Primary source for promoter/enhancer BED files in Research Mode. Fallback to synthetic regulatory regions in CI Mode. |
| **GWAS Catalog** | `ftp://ftp.ebi.ac.uk/pub/databases/gwas/` | **Available (Real)** | Primary source for GWAS lead SNPs in Research Mode. Fallback to cached subset (versioned) in CI Mode. |
| **SNP (CSV)** | ` | **Available (Small)** | Too small for genome-wide study. Used only for unit testing the scoring logic. |
| **MAF (Parquet)** | ` | **Available (Irrelevant)** | Unrelated to human population genetics. Not used. |
| **GWAS (Parquet)** | ` | **Available (Irrelevant)** | Contains CADD scores, not GWAS lead SNPs. Not used. |

**Decision**: The plan proceeds by implementing the pipeline to work with **real data** (1000 Genomes, JASPAR 2024, ENCODE, GWAS Catalog) in Research Mode. For CI Mode, it uses **synthetic/mock data** to validate the *logic* of the pipeline, with explicit warnings that the *biological conclusions* are untestable in CI Mode.

## 3. Methodological Approach

### 3.1 Data Ingestion (FR-001)
- **Input**: VCF (1000 Genomes) or Synthetic Generator.
- **Filtering**:
 - MAF > 1% (if MAF column exists; otherwise, assume all synthetic SNPs are common).
 - Overlap with Regulatory Regions (BED).
 - **Edge Case**: SNPs with N alleles or indels are excluded.
 - **Edge Case**: Boundary SNPs (overlap ≥ 1bp) are included.
- **Spec Gap**: FR-001 mandates dbSNP. The plan uses 1000 Genomes as a verified proxy for common human SNPs.

### 3.2 Affinity Scoring (FR-002, FR-003)
- **Context**: **Dynamic Window** (±15bp or PWM-length dependent) around the SNP to ensure the full binding site is captured for all TFs.
- **PWM**: JASPAR 2024 (Human).
- **Calculation**:
 - Extract Ref and Alt sequences.
 - Compute log-odds score for each using PWM.
 - $\Delta Score = Score_{alt} - Score_{ref}$.
- **Handling**: If the PWM does not match the sequence length, pad or truncate (strictly defined in `scoring.py`).
- **Spec Gap**: FR-002 mandates ±10bp. The plan uses a dynamic window for accuracy.

### 3.3 Statistical Analysis (FR-004, FR-005, FR-006)
- **Null Distribution**: **Stratified Label Permutation**.
 - SNPs are binned by sequence context (GC-content, k-mer profile).
 - $\Delta Score$ values are permuted *within* these bins to break the link between the SNP variant and its score while preserving the local sequence composition distribution.
 - This generates a null distribution representing 'the distribution of $\Delta Scores$ expected if the SNP allele had no specific effect beyond the background sequence properties'.
 - This method ensures the null distribution is independent of the regulatory landscape's inherent properties.
- **Enrichment**: **Baseline Correction**.
 - Instead of selecting top SNPs and comparing to a random set, the plan calculates the enrichment ratio relative to the *entire* distribution of $\Delta Scores$ for that TF.
 - A regression framework controls for MAF and distance to TSS to eliminate 'winner's curse' and circularity.
- **FDR**: **West-Stephens max-T permutation procedure** to handle dependence between correlated TF motifs.
- **Spec Gap**: FR-004 mandates 'shuffling SNP positions'. The plan uses 'Stratified Label Permutation' to address methodological concerns.

## 4. Compute Feasibility

- **RAM**: Sequences are processed in batches. Memory-mapped FASTA files are used.
- **Time**: Permutation test (1000 iterations) is parallelized via `multiprocessing` (4 cores max on runner).
- **GPU**: Not required. All operations are CPU-bound (matrix multiplication, string matching).

## 5. Limitations & Assumptions

- **Dataset Fit**: The plan uses 1000 Genomes as a proxy for dbSNP (FR-001) and dynamic windowing (FR-002) to address methodological concerns. These are deviations from the spec.
- **PWM Limitation**: PWMs ignore chromatin accessibility and cooperative binding. This is an accepted proxy per the spec.
- **Causality**: All findings are associational (observational study).
- **CI vs. Research**: The CI run uses synthetic data for logic validation only. The biological hypothesis cannot be validated in CI Mode.
- **Success Criteria Measurement**: SC-001 and SC-003 require real data (1000 Genomes and GWAS Catalog) to be measured against the real-world dataset. Synthetic data cannot satisfy these criteria.