# Research: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Executive Summary

This research outlines the data strategy, statistical methodology, and computational feasibility for analyzing gene regulation mechanisms across five cell types. The primary challenge is sourcing high-quality ATAC-seq/ChIP-seq peak data from ENCODE and performing motif enrichment analysis within strict CPU-only resource limits.

## Dataset Strategy

### Primary Data Source: ENCODE

The project requires ATAC-seq and ChIP-seq peak files for GM12878, K562, HepG2, H1-hESC, and IMR90 from the ENCODE project.

**CRITICAL DATASET MISMATCH WARNING**:
The provided "# Verified datasets" block in the project configuration **does not contain any verified URLs for ENCODE ATAC-seq or ChIP-seq peak data**. The listed URLs (e.g., `RamAnanth1/lex-fridman-podcasts`, `flxclxc/encoded_drug_reviews`) are unrelated to genomic data (they are podcasts, drug reviews, etc.).

**Action Plan**:
1.  **Do NOT fabricate a URL.** The plan cannot proceed with a verified download link from the provided list.
2.  **Implementation Strategy**: The `code/ingest/download.py` script will be designed to fetch data from the **official ENCODE public download portal** (e.g., `https://www.encodeproject.org/files/...`) using accession IDs specified in the spec.
3.  **Verification**: The `research.md` and `data-model.md` will document the *expected* accession IDs (to be filled by the researcher during the "Clarified" stage or fetched dynamically via the ENCODE API if the API is accessible without auth).
4.  **Fallback**: If the ENCODE API is rate-limited or inaccessible, the system will rely on the user providing the raw files in `data/raw/` manually, as per the "Assumptions" in the spec.

**Dataset Table (Placeholder for Implementation)**:

| Dataset | Source | Accession ID (Example) | Format | Verified URL (from Spec Block) | Status |
| :--- | :--- | :--- | :--- :--- | :--- |
| ENCODE Peaks (GM12878) | ENCODE | ENCFF... | BED | *None available in verified list* | **Manual/API Fetch Required** |
| ENCODE Peaks (K562) | ENCODE | ENCFF... | BED | *None available in verified list* | **Manual/API Fetch Required** |
| ... (others) | ... | ... | ... | ... | ... |

*Note: The implementation will use the official ENCODE API or direct public links. The "Verified datasets" block provided is insufficient for this domain and must be overridden by the implementation team using the official ENCODE portal.*

### Background Model Strategy

To avoid tautological enrichment, the background model will consist of Peak Regions from *other* cell types. For example, when testing enrichment in GM12878, the background will be the union of peaks from K562, HepG2, H1-hESC, and IMR90. This isolates cell-type-specific signals.

### Independent Validation Data

For cross-validation (US-3), the system will attempt to fetch ChIP-seq peaks for the top identified TFs in the same cell type from ENCODE or GEO. Similar to the primary data, no verified URL exists in the provided list. The code will implement a robust fetcher for the official ENCODE portal.

## Statistical Methodology

### 1. Motif Scanning (FR-003)

*   **Tool**: `FIMO` (part of MEME Suite) is chosen for CPU tractability and standard usage.
*   **Database**: JASPAR 2024 (core collection).
*   **Threshold**: p-value ≤ 0.0001.
*   **Handling Zero Matches**: If a motif has no matches in a cell type, the p-value is set to 1.0, and a flag `no_matches` is set. This prevents division-by-zero errors in enrichment.

### 2. Enrichment Analysis (FR-004)

*   **Test**: Fisher's Exact Test (2x2 contingency table).
    *   Rows: Motif Present / Motif Absent.
    *   Columns: Target Cell Type Peaks / Background Peaks.
*   **Multiple Testing Correction**: Benjamini-Hochberg (BH) procedure applied to all (Motif x Cell Type) combinations to control False Discovery Rate (FDR).
*   **Significance**: q-value < 0.05.

### 3. Clustering & Visualization (FR-005)

*   **Distance Metric**: Euclidean distance on the matrix of -log10(q-values).
*   **Clustering**: Hierarchical clustering (Ward's method).
*   **Validation**: Silhouette score ≥ 0.4 required for the heatmap clusters. If < 0.4, the plot is generated but flagged as "low separation".

### 4. Cross-Validation (US-3)

*   **Metric**: Overlap percentage between predicted motif peaks and independent ChIP-seq peaks.
*   **Threshold**: ≥ 60% overlap for top hits to claim biological relevance.
*   **Caveat**: Since the study is observational, claims are framed as "associational" (Constitution Principle I).

## Compute Feasibility & Resource Planning

### Constraints
*   **CPU**: 2 cores.
*   **RAM**: ~7 GB.
*   **Disk**: 14 GB.
*   **Time**: 6 hours.

### Mitigation Strategies
1.  **Sampling**: If the raw peak files exceed memory limits during annotation, the `parse.py` script will process files in chunks (streaming) or downsample if necessary (though the spec assumes full processing).
2.  **FIMO Optimization**: Use `--max-p-value` and `--motif-pseudocounts` to speed up scanning. Run FIMO with `--threads 2` (max allowed).
3.  **Memory Management**: Use `pandas` with appropriate dtypes (e.g., `int32` for coordinates) and `numpy` for matrix operations. Avoid loading all peak coordinates into a single massive DataFrame if possible; process per cell type.
4.  **Disk Cleanup**: Intermediate files (e.g., temporary BED files for FIMO) are deleted immediately after processing. `TMP_DIR` is checked for ≥1GB free space before start.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **ENCODE API Rate Limits** | High (Download fails) | Implement exponential backoff (3 retries) as per FR-006. |
| **Missing Verified URLs** | High (Data unavailable) | Code supports manual file drop-in if API fetch fails. |
| **Disk Space Exhaustion** | High (Pipeline crash) | Pre-flight check for ≥14GB; delete temp files aggressively. |
| **FIMO Too Slow** | Medium (Timeout) | Limit to top 500 motifs or sample peaks if runtime > 4h. |
| **No Cell-Type Specificity** | Medium (Null result) | Silhouette score < 0.4 is a valid outcome; report "no clear clustering". |
