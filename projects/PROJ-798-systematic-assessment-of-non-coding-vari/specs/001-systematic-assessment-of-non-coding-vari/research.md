# Research: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Problem Statement & Hypothesis
**Hypothesis**: Common non‑coding SNPs that reside in promoters/enhancers and substantially alter PWM‑derived binding affinities (|Δ Score| ≥ 2 bits) are enriched among GWAS Catalog lead SNPs relative to a GC‑matched non‑regulatory control set.

The study is **observational**; all conclusions are framed as associational.

## 2. Dataset Strategy
Only **open, programmatically downloadable** sources are used (as required by the CI runner). When a spec‑listed source lacks a verified HuggingFace mirror, the canonical FTP/HTTP URL from the spec is employed.

| Dataset | Content | Canonical URL (from spec) | Verification Status |
|---------|---------|---------------------------|---------------------|
| dbSNP (common, MAF > 1 %) | Human SNP VCF (GRCh38) | `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/` | No verified mirror; used as‑is |
| JASPAR 2024 PWMs | Human TF PWMs | ` (direct download) | No verified mirror; used as‑is |
| ENCODE/Roadmap promoters & enhancers | BED intervals | `ftp://ftp.ebi.ac.uk/pub/databases/encode/` (v4) | No verified mirror; used as‑is |
| GWAS Catalog lead SNPs | BED of lead SNP positions | `ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/` | No verified mirror; used as‑is |
| Sample CSV for unit tests | Small SNP table | ` | Verified |
| Sample GWAS Parquet for unit tests | Small GWAS table | ` | Verified |

**Fallback**: If any primary FTP source is unreachable, the pipeline aborts with a clear error (no fabricated data).

## 3. Methodology & Statistical Rigor

### 3.1 Data Ingestion & Filtering (FR‑001)
1. **Streaming download** of the dbSNP VCF to keep RAM < 7 GB.  
2. **MAF filter** (`MAF > 0.01`).  
3. **LD pruning** (r² < 0.1) using `pysam`/`plink`‑style window; each SNP receives an `ld_block_id`.  
4. **Stratification assignment**: Each SNP is assigned a `stratum_id` that is a composite of its GC‑content bin (e.g., 0.4–0.45), distance‑to‑TSS bin (e.g., 0–1 kb, 1–10 kb, etc.), and optionally a DNase‑I hypersensitivity bin (when available). This stratification preserves local genomic structure and baseline regulatory enrichment during permutation.  
5. **Regulatory overlap** via `pybedtools` (≥ 1 bp overlap).  
6. **GC‑matched control**: for every regulatory SNP, a random non‑regulatory region is sampled with GC content ± 2 % and the same `ld_block_id` and `stratum_id` to preserve local correlation structure and stratification.  
7. **Checksums** recorded for all raw and derived files.

### 3.2 PWM Loading & Affinity Scoring (FR‑002, FR‑003)
* Load all human PWMs from JASPAR 2024, discarding motifs < 6 bp or with low information content.  
* **Biophysical proxy limitation** – PWMs are a coarse model; we acknowledge this and will perform a **sensitivity analysis** using only high‑information PWMs (IC ≥ 1.5 bits per position) and optionally incorporating DNase‑I hypersensitivity scores as a covariate in downstream checks.  
* For each SNP‑TF pair: extract a sequence window of length = PWM length, centered on the variant (using `pyfaidx` on the GRCh38 reference).  
* Compute log‑odds scores for reference and alternate alleles; Δ Score = Score_alt − Score_ref.  
* Flag `is_large_magnitude` when |Δ Score| ≥ 2 bits (report‑only).

### 3.3 Enrichment Testing (FR‑004 → FR‑008)

#### Stratification & Confound Control
* Each SNP is assigned a `stratum_id` based on GC‑content bins, distance‑to‑TSS bins, and optionally DNase‑I hypersensitivity bins. This ensures that permutations preserve baseline regulatory enrichment and do not allow chromatin accessibility, TF expression proxies, or positional biases to drive spurious enrichment.
* The GC‑matched control set is generated such that each control region shares the same `ld_block_id` and `stratum_id` as its matched regulatory SNP, ensuring that the control set is not only GC‑matched but also stratified identically.

#### KS Test (General Shift)
* Compare the Δ Score distribution of SNPs **inside** GWAS loci **against the GC‑matched non‑regulatory control set** (NOT against raw "outside GWAS" SNPs, which may themselves be enriched for regulatory features) using a **block‑aware, stratified permutation KS**: 
  - For each of **500** permutations, GWAS labels are shuffled **only within each (LD block, stratum) pair**, preserving LD dependence and stratification.
  - The KS statistic is recomputed on each shuffled label set.
  - The empirical p‑value is the proportion of permuted statistics ≥ observed.
* A secondary KS comparison using the GC‑matched control set is performed and reported in the results summary for robustness.
* This design ensures the reference distribution is uncontaminated by regulatory enrichment of the "outside GWAS" SNPs.

#### Tail‑Enrichment Test (Specific Disruption)
* Proportion test (Fisher's exact) on the count of SNPs with |Δ Score| ≥ 2 bits inside vs. outside GWAS loci.  
* **Threshold sensitivity** – we will repeat the tail test for |Δ Score| thresholds of multiple bit levels including lower, moderate, and higher magnitudes and report how results vary.

#### Permutation Strategy (FR‑004, FR‑006)
* **N = 500** permutations.  
* In each permutation, GWAS labels are shuffled **within each (LD block, stratum) pair** to preserve local correlation, GC bias, TSS distance bias, and optional chromatin accessibility bias.  
* The same shuffled label set is used for **all TFs** simultaneously, enabling West‑Stephens max‑T FDR correction.  
* **Family‑wise error** is controlled by the max‑T approach; the minimal attainable p-value is very small (acknowledged as exploratory).

#### FDR Correction (FR‑006)
* Compute the maximum KS statistic across TFs for each permutation → empirical null distribution of maxima.  
* Corrected p‑value for each TF = proportion of permutations where max‑T ≥ observed KS statistic.  

#### Significance Threshold (FR‑008)
* Apply α = 0.05 (corrected) – as verified from the Wikipedia source on p‑values (https://en.wikipedia.org/wiki/P-value).  

### 3.4 Power & Limitations
* With a large number of permutations the smallest non‑zero p‑value is 0.002; results near this bound are reported as **exploratory**.  
* TFs with a minimal number of scored SNPs are excluded from permutation testing (reduces multiple‑testing burden).  
* **Compute feasibility** – we limit the analysis to a subset of the most informative PWMs (IC ≥ 1.5 bits) and, if the full SNP set exceeds memory limits, we sub‑sample to a reduced set of SNPs. This keeps runtime ≤ 6 h on a 2‑CPU runner.

## 4. Compute Feasibility (CPU‑first)
* **Batch size**: 50 k SNP‑TF pairs per chunk (≈ 200 MB RAM).  
* **Permutation loop**: vectorized NumPy operations; total runtime estimated ≤ 5 h on 2 CPU cores with the TF and SNP limits above.  
* No GPU required; all libraries run on CPU.  

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| FTP source unreachable | Pipeline aborts | Clear error message; no fallback to synthetic data. |
| OOM on VCF parsing | Job failure | Streaming, chunked processing, memory‑mapped Parquet outputs. |
| Insufficient permutation power | False negatives | 500 permutations; sensitivity analysis across thresholds; report exploratory nature. |
| LD‑block & stratum shuffling bug | Inflated Type I error | Unit test verifies that label counts per (block, stratum) pair are preserved after each shuffle. |
| Uncontrolled genomic confounds | Biased enrichment | Stratified GC‑matched control generation, stratified permutation (GC/TSS/chromatin bins), optional covariate adjustment using DNase‑I hypersensitivity. |
| PWM coarse proxy | Mis‑measurement of true affinity | Sensitivity analysis using high‑information PWMs; explicit limitation discussion. |
| KS independence violation | Inflated Type I error | Block‑aware, stratified permutation KS p‑value preserves LD and confound structure. |
| Control set contamination | Biased reference distribution | GC‑matched control set is used as the reference; "outside GWAS" SNPs are excluded from KS test. |

---