# Research: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Problem Statement & Hypothesis

**Hypothesis**: Non-coding SNPs located in regulatory regions that disrupt transcription factor (TF) binding motifs are enriched in GWAS loci for complex traits compared to SNPs in non-regulatory regions or control sets.

**Key Challenge**: The analysis requires integrating massive genomic datasets (dbSNP, ENCODE, GWAS) and performing computationally intensive scoring (millions of SNP-TF pairs) on limited hardware (a constrained CPU configuration and restricted RAM).

## 2. Dataset Strategy

The following datasets are required. Per the project constraints, only verified sources from the provided list are cited. For datasets without a verified source in the list, the plan uses the canonical URLs specified in the `spec.md` and explicitly notes the lack of a verified HuggingFace mirror.

| Dataset | Description | Source / URL | Status |
|:--- |:--- |:--- |:--- |
| **dbSNP (Common)** | Human SNPs (GRCh38, MAF > 1%) | `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/` | **NO verified source found** (Specified FTP path used). Fallback: 1000 Genomes Phase 3. |
| **JASPAR 2024** | Human TF Position Weight Matrices (PWMs) | ` (Direct download) | **NO verified source found** (Specified HTTP path used). |
| **ENCODE/Roadmap** | Promoter/Enhancer BED files | `ftp://ftp.ebi.ac.uk/pub/databases/encode/` (or similar) | **NO verified source found** (Specified FTP path used). |
| **GWAS Catalog** | Lead SNPs for enrichment analysis | `ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/` | **NO verified source found** (Specified FTP path used). |
| **Reference: SNP (csv)** | Sample SNP data (for unit tests only) | ` | Verified. **Schema-Mirrored**: Manually curated to match production EBI/NCBI column structure (rsID, chr, pos, ref, alt) to ensure unit test validity. |
| **Reference: GWAS (parquet)** | Sample GWAS data (for unit tests only) | ` | Verified. **Schema-Mirrored**: Manually curated to match production EBI/NCBI column structure (rsID, chr, pos, ref, alt) to ensure unit test validity. |

**Critical Note on Data Availability**: The primary analysis relies on the canonical FTP sources listed in the `spec.md`. The "Verified datasets" block provided for this task does not contain a direct HuggingFace mirror for the full dbSNP build 155, JASPAR 2024, or ENCODE/Roadmap BED files. The implementation will fetch directly from the canonical FTP/HTTP sources as per the spec. If these sources are unreachable, the pipeline will fail with a clear error, adhering to the "Verified Accuracy" principle (no fabricated URLs).

## 3. Methodology & Statistical Rigor

### 3.1 Data Ingestion & Filtering (FR-001)
1. **Fetch**: Download common SNPs (MAF > 1%) from dbSNP build 155.
 * **Fallback Strategy**: If the full dbSNP VCF fetch fails or times out, automatically switch to the 1000 Genomes Phase 3 common variants subset (smaller, more stable) and log the switch.
 * **Chunking**: Download in chunks to prevent OOM. Verify checksums.
2. **LD Pruning & Block Definition**:
 * Perform LD pruning (r² < 0.1) to identify a set of independent index SNPs.
 * **Crucially**, group all SNPs (both index and pruned) into **LD Blocks** based on their proximity to the nearest index SNP (within a 250kb window). This defines the correlation structure.
 * This step ensures that the "full unfiltered distribution" used in the KS test respects the non-independence of variants, and provides the unit for stratified permutation.
3. **Filter**: Intersect SNPs with ENCODE/Roadmap BED files (promoters/enhancers).
4. **Control Generation**: Generate a GC-matched non-regulatory control set.
 * **Stratified Matching**: For each regulatory SNP, sample a random genomic region with:
 * Same GC content (±2%).
 * Same TSS distance bin (±1kb bins).
 * Same LD Block ID (to preserve local correlation structure).
 * *Validation*: Verify overlap counts and GC/TSS/LD-distribution similarity.

### 3.2 Affinity Scoring (FR-002, FR-003)
1. **Load PWMs**: Parse JASPAR 2024 matrices. Filter to a curated set of high-confidence human motifs (exclude low-confidence/short motifs).
2. **Score**: For each SNP, extract the sequence window (length = PWM length) for both Ref and Alt alleles.
3. **Calculate**: Compute $\Delta Score = Score_{alt} - Score_{ref}$ (log-odds).
4. **Flag**: Set `is_large_magnitude` if $|\Delta Score| \ge 2$ bits.
 * *Constraint*: Do NOT filter data based on this flag; use only for reporting.

### 3.3 Statistical Enrichment (FR-004 - FR-008)
**Dual-Test Strategy**:
1. **KS Test (General Shift)**: Compare the observed $\Delta Score$ distribution (in-GWAS) vs. (out-of-GWAS) using the Kolmogorov-Smirnov test. This satisfies FR-005's requirement for "full unfiltered distribution" analysis.
2. **Tail-Enrichment Test (Specific Disruption)**: Perform a Proportion Test (Fisher's Exact or Z-test) on the fraction of SNPs with $|\Delta Score| \ge 2$ bits. This addresses the specific "enrichment of large disruptions" hypothesis where KS may lack power.

**Permutation & FDR (West-Stephens max-T)**:
1. **TF Filtering**: Only perform permutation tests on TFs with ≥50 scored SNPs in the regulatory set. This reduces the multiple-testing burden from ~1000 to ~100-200, improving the stability of the max-T estimation within the N=100 constraint.
2. **Null Distribution**: Perform $N=100$ permutations.
 * **Mechanism**: In **each** of the 100 iterations, a **SINGLE** random permutation of GWAS labels is applied to the **entire** SNP dataset. This label set is then used to recalculate the KS statistic (and Tail statistic) for **ALL** TFs simultaneously. This preserves the joint distribution of test statistics across correlated TFs.
 * **Stratified Permutation (Addressing LD Bias)**: To prevent Type I error inflation due to LD, label shuffling is **NOT** performed globally. Instead, GWAS status labels are shuffled **independently within each LD Block** and **within each GC-content/TSS-distance stratum**.
 * *Rationale*: This ensures that the null distribution preserves the local correlation structure (LD) and genomic confounding factors (GC/TSS) of the observed data. A SNP and its neighbors in the same LD block will effectively swap GWAS status together or remain together, preventing the artificial breaking of correlation structures that would bias the null.
3. **FDR Correction**: Apply West-Stephens max-T permutation FDR correction across all tested TFs.
 * *Method*: The max-T statistic for each permutation is the maximum KS statistic observed across all TFs. The p-value for each TF is the proportion of permutations where the max-T statistic exceeds the observed KS statistic for that TF.
4. **Threshold**: Significance at $\alpha = 0.05$ (corrected).
5. **Limitation**: Acknowledge that with N=100, the minimum achievable p-value is 0.01. Results are considered "exploratory" if p-values are near this threshold.

## 4. Compute Feasibility & Constraints

- **Hardware**: 2 CPU, 7 GB RAM, No GPU.
- **Strategy**:
 - **Batching**: Process SNPs in chunks (e.g., tens of thousands at a time) to stay within RAM limits.
 - **Permutations**: Limited to 100 as per spec (NFR-001) to ensure runtime < 6 hours.
 - **TF Filtering**: Limit to a subset of high-confidence TFs to reduce runtime.
 - **Libraries**: Use `scipy.stats.ks_2samp` and `numpy` for vectorized operations. Avoid heavy deep learning frameworks.
 - **Memory**: Use memory-mapped files or generators for large VCF/BED files.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Data Source Unreachability** | Pipeline fails. | Use canonical FTP URLs from spec. If 404, fallback to 1000 Genomes subset. |
| **Memory Overflow** | OOM on CI runner. | Implement strict chunking (large batches of SNPs) and garbage collection. |
| **Runtime Exceedance** | Job timeout. | Limit permutations to 100. Profile code early. Filter TFs to high-confidence set. |
| **Statistical Power** | Low power with N=100. | Acknowledge limitation in report; use Tail-Enrichment test for specific hypothesis. |
| **LD Bias** | Anti-conservative p-values. | **Implemented Stratified Permutation**: Labels are shuffled within LD blocks and GC strata to preserve correlation structure. |