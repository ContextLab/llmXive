# Research: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Dataset Strategy

The primary data source is the **ENCODE Project** (Encyclopedia of DNA Elements), which provides standardized, high-quality ATAC-seq and ChIP-seq peak data for the five specified cell types.

**Verified Datasets**:
*Note: The "Verified datasets" block in the prompt contained non-ENCODE URLs (drug reviews, Yelp, CelebA) which are irrelevant to this genomic study. The plan below strictly adheres to the ENCODE specification (FR-001) by using the official ENCODE download API, which is the canonical source for these files. The URLs in the prompt's "Verified datasets" block are NOT used for this project as they do not contain genomic peak data.*

**Data Acquisition Strategy**:
1.  **Source**: ENCODE Project (https://www.encodeproject.org/).
2.  **Method**: The `code/download.py` script will use the ENCODE public API to fetch peak files for the Several cell types (GM12878, K562, HepG2, H1-hESC, IMR90).
3.  **Accession Mapping**: The script will query the ENCODE API for `experiment_type`="ATAC-seq" or `experiment_type`="ChIP-seq" and `biosample_term_name` matching the target cell types.
4.  **File Selection**: For each cell type, the script will select the "replicate" or "pooled" peak file with the highest `annotation_score` (typically 1) and `file_format`="BED".
5.  **Handling 403/Rate Limits**: The script implements **FR-006**: Exponential backoff (1s, 2s, 4s) with a maximum of 3 retries. If the ENCODE API returns 403 (Forbidden) after retries, the script logs a specific error and aborts *that specific file* but continues if possible, or fails the run if critical data is missing. This adheres to the spec's requirement for robustness without inventing new constraints.
6.  **Background Model (CRITICAL ALIGNMENT WITH FR-004)**:
    *   **Strategy**: The background model is **NOT** random genomic regions. As mandated by FR-004 and the Spec Assumptions, the background for Cell Type A is the **Union of Peak Regions from the other four cell types** (B, C, D, E).
    *   **Rationale**: This ensures the background represents "accessible chromatin" generally, avoiding the confounding of heterochromatin regions. It tests for *differential* enrichment (is this motif more specific to A than to the rest?) rather than absolute enrichment.
    *   **Implementation**: `code/preprocess.py` will aggregate the parsed BED files of the 4 non-target cell types into a single `background_union.bed` file for the target cell type. No random generation or GC-matching is performed.
    *   **Determinism**: The aggregation is deterministic based on the input files.

**Motif Database**:
*   **Source**: JASPAR 2024 (or latest available via `jaspar` Python package).
*   **Format**: MEME format (compatible with FIMO).
*   **Version Tracking**: The specific JASPAR release version will be recorded in `data/provenance.json` (Constitution VII).

## Statistical Methodology

### 1. Motif Scanning (FR-003)
*   **Tool**: FIMO (Find Individual Motif Occurrences) from the MEME suite.
*   **Threshold**: P-value ≤ 0.0001 (as per spec).
*   **Input**: Processed BED files of peaks for each cell type.
*   **Output**: BED file of motif matches with coordinates, motif ID, p-value, and q-value (initially).

### 2. Enrichment Analysis (FR-004) - Differential Enrichment
*   **Method**: Fisher's Exact Test.
*   **Null Hypothesis**: The motif is equally likely to occur in the peaks of Cell Type A as in the union of peaks from the other cell types.
*   **Contingency Table Construction**:
    *   **Numerator (a)**: Count of peaks in **Cell Type A** containing Motif M.
    *   **Denominator (b)**: Count of peaks in **Cell Type A** NOT containing Motif M.
    *   **Background Numerator (c)**: Count of peaks in the **Union of Other Cell Types** containing Motif M.
    *   **Background Denominator (d)**: Count of peaks in the **Union of Other Cell Types** NOT containing Motif M.
    *   **Total Peaks (N)**: a + b (Total peaks in Cell Type A).
    *   **Total Background (M)**: c + d (Total peaks in Union of Other Cell Types).
*   **Correction**: Benjamini-Hochberg (BH) procedure applied across all (Motif × Cell Type) tests to control False Discovery Rate (FDR).
*   **Significance Threshold**: q-value < 0.05 (SC-002).

### 3. Multiple Comparison & Power
*   **Correction**: BH correction is explicitly applied.
*   **Power**: Given the observational nature and the large number of peaks (typically >10k), statistical power is high for detecting strong enrichment. The plan acknowledges that weak effects may be missed, but the large sample size (peaks) mitigates Type II error for strong signals.
*   **Causal Inference**: The study is observational. Claims will be framed as "associational" (e.g., "Motif X is enriched in Cell Type A relative to others") rather than causal.

### 4. Visualization & Validation (FR-005, SC-003)
*   **Heatmap**: Clustered by Euclidean distance of q-values. Silhouette score ≥ 0.4 will be calculated to validate cluster quality.
*   **Cross-Validation**: For top enriched motifs (q < 0.05), independent ChIP-seq peaks for the corresponding TF in the same cell type will be retrieved from ENCODE.
    *   **Independence Check**: Ensure the ChIP-seq experiment ID is different from the ATAC-seq experiment ID used for the target cell type.
    *   **Validation Metric**: Instead of a flawed "Overlap Percentage" threshold, we perform a **Fisher's Exact Test** comparing the presence of the motif in the *independent ChIP-seq peaks* vs. a background of *other accessible regions*.
 * **Success Criterion**: The motif is considered validated if the enrichment p-value in the ChIP-seq data is significant (p < 0.05) AND the motif is enriched (odds ratio > 1). The [deferred] overlap is recorded as a "sanity check" statistic but is NOT the primary pass/fail gate.
    *   **Handling No Matches**: If a motif has zero matches in a cell type, the p-value is calculated as 1.0 (consistent with null), and the result is flagged as "no matches found" to prevent crashes.

## Compute Feasibility
*   **Memory**: Peak files are text-based (BED). Even with cell types and A substantial number of peaks each, the in-memory representation is < 100MB. FIMO is CPU-bound but memory-efficient.
*   **Disk**: Total raw download < 1GB. Unpacked/intermediate files < 5GB. Well within 14GB limit.
* **Runtime**: FIMO scanning of genomic regions against a comprehensive motif library takes [deferred] per cell type on 2 CPUs. Total runtime < 2 hours.
*   **GPU**: Not required. FIMO and statistical tests are CPU-native.

## Assumptions & Risks
*   **Assumption**: ENCODE API remains stable and public.
*   **Risk**: ENCODE file format changes. *Mitigation*: Robust parser in `preprocess.py` with error logging (US-1).
*   **Risk**: The union of peaks from other cell types may be too small for a specific cell type if the cell types are very distinct. *Mitigation*: If the union size < 1000 peaks, the analysis for that cell type will be flagged, and the spec's assumption of "sufficient data" will be re-evaluated.
