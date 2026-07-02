# Data Model: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Overview

This document defines the data structures used throughout the pipeline, ensuring consistency between ingestion, processing, and analysis. All data is stored in the `data/` directory hierarchy.

## Data Flow

1.  **Raw**: Downloaded ENCODE BED files (unmodified).
2.  **Interim**: Parsed peaks, GC-matched background regions, FIMO output.
3.  **Processed**: Enrichment matrices, validation statistics, visualization inputs.

## Core Entities

### 1. Peak Region
A genomic interval representing an accessible region.
*   **Fields**: `chromosome` (str), `start` (int), `end` (int), `cell_type` (str), `source_file` (str).
*   **Origin**: ENCODE BED files.
*   **Transformation**: Parsed by `preprocess.py`, annotated with gene symbols.

### 2. Motif Match
A genomic location where a TF motif was found.
*   **Fields**: `chromosome` (str), `start` (int), `end` (int), `motif_id` (str), `p_value` (float), `q_value` (float), `cell_type` (str), `peak_id` (str).
*   **Origin**: FIMO output.
*   **Transformation**: Filtered by p-value ≤ 0.0001.

### 3. Enrichment Result
Statistical summary of motif enrichment.
*   **Fields**: `motif_id` (str), `cell_type` (str), `observed_count` (int), `expected_count` (float), `p_value` (float), `q_value` (float), `odds_ratio` (float).
*   **Origin**: `enrichment.py`.
*   **Transformation**: Aggregated into a matrix for visualization.

### 4. Validation Statistic
Overlap between predicted motifs and independent ChIP-seq data.
*   **Fields**: `motif_id` (str), `cell_type` (str), `chip_see_source` (str), `overlap_percentage` (float), `validation_status` (str: "passed" | "failed" | "no_data").
*   **Origin**: `visualize.py` (validation step).

## File Formats

*   **Input/Intermediate**: BED (6 columns: chrom, start, end, name, score, strand) or TSV.
*   **Processed**: Parquet or CSV for efficient matrix operations.
*   **Provenance**: JSON (`data/provenance.json`).

## Constraints & Validations

*   **Coordinates**: 0-based, half-open (BED standard).
*   **Cell Types**: Must be one of: `GM12878`, `K562`, `HepG2`, `H1-hESC`, `IMR90`.
*   **Motif IDs**: Must match JASPAR 2024 IDs (e.g., `MA0139.1`).
*   **P-values**: Range [0.0, 1.0].
*   **Q-values**: Range [0.0, 1.0], monotonically non-decreasing when sorted by p-value.
