# Data Model: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

## Overview

This document describes the data model for the project, including entities, attributes, relationships, and schemas. The model supports the pipeline from raw data ingestion to final results.

## Entities

### CRE (cis-regulatory element)

- **Description**: Genomic interval derived from merged MACS2 peaks.
- **Attributes**:
  - `cre_id`: Unique identifier (e.g., "CRE_001").
  - `chromosome`: Chromosome name (e.g., "chrI").
  - `start`: Start position (0-based).
  - `end`: End position.
  - `strand`: "+" or "-".
  - `tf`: Associated transcription factor(s) (comma-separated).
  - `context`: "promoter" (≤500 bp upstream) or "distal" (>500 bp).
  - `peak_signal_control`: Normalized RPKM in control condition.
  - `peak_signal_stress`: Normalized RPKM in stress condition.
  - `delta_peak_signal`: `peak_signal_stress - peak_signal_control`. (Used in LMM as predictor).
  - `motif_p_value`: PWM p-value for motif match (if distal).
  - `hic_contact_frequency`: Hi-C contact frequency (if distal).
  - `validation_flag`: "valid" if passes FR-014 (Motif OR Hi-C), "invalid" otherwise.
  - `collinearity_flag`: "collinear" if VIF > 5, "ok" otherwise.
  - `weight`: Log-transformed motif score or Hi-C frequency (if valid). Used as observation-level weight in LMM.

### Gene

- **Description**: Yeast ORF.
- **Attributes**:
  - `gene_id`: ORF name (e.g., "YAL001C").
  - `nearest_cre_id`: ID of nearest CRE (≤10 kb).
  - `expression_fold_change_control`: Expression fold-change in control.
  - `expression_fold_change_stress`: Expression fold-change in stress.
  - `delta_expression`: `expression_fold_change_stress - expression_fold_change_control`.
  - `promoter_binding_score`: Baseline promoter binding score (covariate).
  - `random_intercept`: `u_g` from LMM (output).

### CRE-Gene Pair

- **Description**: Linked CRE and gene for analysis.
- **Attributes**:
  - `pair_id`: Unique identifier (e.g., "PAIR_001").
  - `cre_id`: Foreign key to CRE.
  - `gene_id`: Foreign key to Gene.
  - `delta_peak_signal`: From CRE.
  - `delta_expression`: From Gene.
  - `weight`: From CRE.
  - `beta1`: Fixed effect estimate from LMM.
  - `p_value`: Raw p-value from LRT.
  - `q_value`: Benjamini-Hochberg adjusted p-value.
  - `significant`: Boolean (q_value ≤ 0.05).

## Relationships

- **CRE** `1:N` **CRE-Gene Pair** (one CRE can link to multiple genes).
- **Gene** `1:N` **CRE-Gene Pair** (one gene can link to multiple CREs).
- **CRE-Gene Pair** `1:1` **LMM Result** (one pair has one model result).

## File Formats

- **Raw Data**: FASTQ (ChIP-seq), Parquet (eQTL), BED (Hi-C peaks).
- **Processed Data**: BED (peaks), TSV (matrices), CSV (weights), TSV (vif_flags).
- **Results**: Markdown (ranked tables), PDF (reports), bigWig (tracks).

## Data Flow

1. **Download**: Raw FASTQ, Parquet, BED → `data/raw`.
2. **Preprocess**: Trim, align, call peaks → `data/processed` (BAM, `merged_peaks.bed`).
3. **Annotate**: Merge peaks, add context, validate → `data/processed` (annotated BED).
4. **Filter**: Apply FR-011, FR-012, FR-014 → `data/processed` (filtered TSV, `vif_flags.tsv`).
5. **Weight**: Compute weights → `data/processed` (weights.tsv).
6. **Model**: LMM, LRT, Permutation → `results` (beta estimates, p-values).
7. **Visualize**: bigWig tracks → `results/tracks`.

## Constraints

- **Memory**: Stream large files; process in batches.
- **Disk**: Keep only necessary intermediates; compress where possible.
- **Integrity**: Checksums for raw data; version control for processed data.
- **Validation**: All processed data must pass the corresponding YAML schema before proceeding to the next phase.