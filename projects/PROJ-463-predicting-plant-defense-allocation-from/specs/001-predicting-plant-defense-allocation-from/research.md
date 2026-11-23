# Research: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Problem Statement

How does tissue-specific transcriptomic response to chewing versus piercing-sucking herbivores predict differential allocation of chemical versus physical defense traits across plant species?

## Dataset Strategy

The project relies on publicly available RNA-seq data from NCBI GEO/SRA. Since no single verified dataset in the provided list contains the specific "chewing vs. piercing-sucking" herbivory metadata required, the pipeline must programmatically fetch and filter studies from NCBI based on keywords and metadata.

**Data Acquisition Plan:**
1. **Primary Source**: NCBI GEO/SRA (via `Entrez` and `SRA Toolkit`).
 * **Verified Accession List**: The pipeline first attempts to load a curated list of verified accession IDs (stored in `data/verified_accessions.yaml`) derived from the literature. This list is prioritized to ensure the dataset is appropriate for the specific "chewing vs. piercing" question.
 * **Keyword Search Fallback**: If the verified list is empty or insufficient, the pipeline falls back to programmatic keyword search ("herbivore", "chewing", "piercing"). However, a **Keyword Validation** step cross-references sample metadata against the "Verified Datasets" list to ensure relevance before processing.
 * **Filtering**: Require ≥2 biological replicates per condition, explicit tissue metadata, and **paired** chewing/piercing data for the same species.
 * **Feasibility**: The GitHub Actions runner (limited CPU, constrained RAM) cannot download and process full raw FASTQ sets for 15+ species simultaneously.
 * **Mitigation**: The pipeline will **downsample** all samples to the **median read depth** (to ensure equal sequencing effort and prevent bias against low-expression species) and, if necessary, select a **fixed-seed random sample** of species to fit the compute budget. If <3 valid studies are found, the pipeline halts with "Insufficient Data for Comparative Analysis" (not just a generic error), as the comparative design is fundamentally unfeasible.
2. **Trait Data**:
 * **Primary**: TRY Plant Trait Database (` Name or service not known)"))]).
 * **Fallback**: Phenoscape (`pyphenoscape`), GBIF (`rgbif`).
 * *Constraint*: If >30% of target species lack trait data from all sources, the pipeline halts (FR-011).

**Verified Datasets Reference:**
While the primary raw data is fetched from NCBI, the following verified datasets from the provided list will be used for *validation* or *reference* if applicable, though the core analysis relies on NCBI:
* *Reference for Pathway Aggregation*: The methodology for reducing features to ≤50 aligns with the approach in **arXiv:2607.17405** (verified in "VERIFIED FACTS").
* *No direct "Plant Herbivory RNA-seq" dataset* exists in the provided "Verified datasets" list that matches the specific experimental design (chewing vs. piercing). Therefore, the plan does **not** use a pre-packaged dataset for the main analysis but instead constructs the dataset from raw NCBI sources, adhering to the "open, directly-downloadable" requirement by using the public NCBI API and verified accession IDs.

**Dataset Feasibility & Compute:**
* **CPU-First**: Alignment (HISAT2) and Quantification (featureCounts) are CPU-intensive. The plan uses a **downsampled** subset of FASTQ files (median depth) to stay within 7GB RAM.
* **GPU Escape Hatch**: If the alignment step exceeds a reasonable time threshold or encounters RAM limits on the CPU runner, the pipeline is designed to offload the alignment step to a Kaggle GPU. (via the execution agent's auto-offload mechanism using `kaggle-kernels` CLI).
* **Data Streaming**: `datasets.load_dataset(..., streaming=True)` will be used for any intermediate metadata tables, but raw FASTQs are downloaded via `faster-sra` or `prefetch` in chunks.

## Methodological Rigor

### Statistical Design
1. **Differential Expression**: DESeq2 (via `rpy2` or `pyDESeq2`) with FDR < 0.05 and |log₂FC| > 1.
 * *Multiple Comparisons*: Holm-Bonferroni correction applied to the set of hypothesis tests (FR-010).
 * *Power Analysis*: Performed prior to modeling (FR-016). **N_eff** is calculated using phylogenetic lambda (N_eff = N / (1 + (N-1)*lambda)). If N_eff < required for R²=0.3, α=0.05, β=0.2, the pipeline halts. This accounts for inflated effect sizes due to phylogenetic non-independence.
2. **Feature Engineering**:
 * **Herbivore-Response Vector**: Derived from top DE genes. **Specificity Vector** = (Chewing log2FC) - (Piercing log2FC). This mathematical operation captures the specific signal of chewing vs. piercing, distinct from general stress.
 * **Pathway Aggregation**: KEGG/GO mapping to reduce 200 genes to ≤50 pathway scores (FR-012). **Biosynthetic pathways** for target traits (Glucosinolates, Alkaloids, Phenolics) are **excluded** to prevent data leakage (tautology).
 * **General Stress Control**: If abiotic stress controls are available, the response vector is adjusted by subtracting the general stress response (abiotic vs control) to isolate the specific herbivore signal. If not, the signal is framed as "Herbivore-Specific + General Stress" and causal claims are limited.
3. **Modeling**:
 * **Algorithms**: Elastic Net and Random Forest.
 * **Validation**: **Clade-Stratified Leave-One-Species-Out (LOSO)** Cross-Validation. Folds are constructed to ensure the test species is phylogenetically distinct from the training set.
 * **Phylogenetic Control**: PGLS validation and phylogenetic null model (shuffling labels on the tree) to ensure R² is not due to shared ancestry (FR-017). The null model shuffles labels while preserving trait-phylogeny structure to distinguish predictive power from shared history.
 * **Stability**: **Bootstrapped Confidence Intervals** on the LOSO mean performance (1000 resamples). This addresses the single-point variance issue of LOSO with N < 15.
4. **Significance Testing**:
 * Permutation test (N=10,000) on the defense allocation index (FR-008).
 * Family-wise error correction for multiple tissue-specific models.
 * **Specificity Test**: Compare chewing-piercing signal against general stress signal (if abiotic controls available).

### Dataset-Variable Fit
* **Requirement**: The dataset must contain transcriptomic data for **chewing** and **piercing-sucking** herbivores, **tissue** metadata, and **replicates**.
* **Risk**: Public datasets often lack explicit "chewing vs. piercing" labels or have mixed herbivore types.
* **Mitigation**: The metadata verification step (T011a) will parse study descriptions and sample annotations for these keywords. Studies failing this are excluded. If no studies match, the pipeline halts with a "No valid data" error (no fabrication).

### Limitations
* **Sample Size**: The number of species with both transcriptomic and trait data is likely small (<15). Power analysis is critical.
* **Observational Nature**: Findings are associational. Causal claims are avoided (Assumption in spec).
* **Batch Effects**: ComBat-seq may not fully correct for platform differences; residual variance >15% triggers exclusion. **Batch-Design Check**: ComBat-seq is only applied if batch != species. If confounded, 'Study' is included as a random effect in PGLS.
* **Underpowering**: With N < 15 and p = 50, the model is underpowered. The plan uses **Clade-Stratified LOSO** and **PVR** baseline to mitigate this. The R² metric is framed as a descriptive statistic with bootstrapped CIs, not a definitive predictive claim.

## Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **NCBI GEO/SRA as Primary Source** | No single pre-packaged dataset in the verified list matches the specific "chewing vs. piercing" herbivory criteria. NCBI is the only open, programmatic source for raw RNA-seq. |
| **Median Depth Downsampling** | Full raw FASTQ downloads for multiple species exceed the 7GB RAM / 14GB disk limit. Downsampling to median depth ensures equal sequencing effort and prevents bias against low-expression species. |
| **Pathway Aggregation (≤50 features, Exclude Biosynthetic)** | With N < 15 species, using 200+ gene features leads to overfitting. Aggregation to pathways (KEGG/GO) is a standard dimensionality reduction technique (cited in arXiv:2607.17405). Excluding biosynthetic pathways prevents tautology. |
| **Clade-Stratified LOSO + Phylogenetic Null** | Standard CV is invalid due to phylogenetic non-independence. LOSO and phylogenetic shuffling are required to validate predictive power (FR-007, FR-017). Clade-stratification ensures test species are phylogenetically distinct. |
| **Hard Halt on Missing Traits** | FR-011 mandates a halt if >30% of species lack traits. This prevents modeling on incomplete data, ensuring the "Defense Allocation Index" is valid. |
| **No Star Phylogeny Fallback** | A star phylogeny invalidates the null model required by SC-006. If the tree fetch fails, the pipeline halts. |
| **Power Analysis with Phylogenetic Lambda** | Generic R² targets are inflated by phylogenetic signal. Power analysis uses N_eff adjusted by lambda to account for this. |
| **Bootstrapped LOSO** | Single-point test sets in LOSO provide no variance estimate. Bootstrapping provides a confidence interval on the mean performance. |
| **General Stress Control** | To distinguish specific herbivore response from general stress, the plan adjusts the response vector if abiotic controls are available. |
| **Batch-Design Check** | ComBat-seq fails if batch == species. If confounded, random effects in PGLS are used instead. |

