# Data Model: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

## Entity Definitions

### 1. Raw Input (ChIP‑seq)
* **Entity**: `ChIPRun`
* **Attributes**:
  * `run_id`: Unique identifier (e.g., SRR123456).
  * `tf`: Transcription Factor name (Hsf1, Msn2, Msn4, Hog1).
  * `condition`: Stress type (heat_shock, osmotic, oxidative, control).
  * `fastq_path`: Path to raw FASTQ.
  * `md5`: MD5 checksum of the FASTQ file.

### 2. Processed Alignment
* **Entity**: `Alignment`
* **Attributes**:
  * `run_id`: FK to `ChIPRun`.
  * `bam_path`: Path to aligned BAM.
  * `mapq_filter`: Boolean (True if MAPQ ≥ 30).
  * `uniquely_mapped_count`: Integer.

### 3. Cis‑Regulatory Element (CRE)
* **Entity**: `CRE`
* **Attributes**:
  * `cre_id`: Unique ID (e.g., CRE_001).
  * `chromosome`: String (e.g., "chrI").
  * `start`: Integer (0‑based).
  * `end`: Integer.
  * `context`: Enum ("promoter", "distal").
  * `associated_tfs`: List of strings.
  * `peak_signal_control`: Float (RPKM/Reads).
  * `peak_signal_stress`: Float.
  * `delta_peak_signal`: Float (Stress − Control).
  * `nearest_gene`: String (ORF).
  * `motif_score`: Float (TF‑motif match confidence, 0‑1). *Optional*; used for weighting in the mixed model.
  * `validated_by_atac`: Boolean – **True** only if the CRE overlaps an ATAC‑seq peak (or if ATAC is missing, this is set to False in "ATAC-Deferred Mode").

### 4. eQTL / Expression
* **Entity**: `ExpressionProfile`
* **Attributes**:
  * `gene_id`: String (Yeast ORF).
  * `log2fc_heat`: Float.
  * `log2fc_osmotic`: Float.
  * `log2fc_oxidative`: Float.
  * `promoter_binding_score`: Float.

### 5. Statistical Result (per CRE‑gene pair)
* **Entity**: `CREAnalysisResult`
* **Attributes**:
  * `cre_id`: FK to `CRE`.
  * `gene_id`: FK to `ExpressionProfile`.
  * `stress_condition`: Enum ("heat_shock", "osmotic", "oxidative").
  * `beta_1_raw`: Float (LMM fixed‑effect estimate for ΔPeakSignal).
  * `beta_1_simex`: Float (SIMEX‑corrected β₁).
  * `measurement_error_variance`: Float (estimated λ used in SIMEX; derived as described in Phase 2.2).
  * `p_value_raw`: Float.
  * `p_value_adj`: Float (Benjamini–Hochberg FDR).
  * `vif_score`: Float (variance inflation factor for predictors).
  * `is_collinear`: Boolean (True if VIF > 5).
  * `is_significant`: Boolean (q ≤ 0.05 after BH correction).
  * `empirical_p_value`: Float (from 10 000 permutations).
  * `motif_score`: Float (copied from CRE for reference).
  * `summit_match_flag`: Boolean (True if summit within ±5 bp of bigWig peak for top‑10 CREs).
  * `validation_status`: Enum ("validated", "unvalidated") – reflects whether ATAC validation succeeded (must be "validated" for any result to be retained in "ATAC-Validated Mode"; in "ATAC-Deferred Mode", all are "unvalidated").

## Data Flow

1. **Ingest**: `ChIPRun` → `Alignment`.
2. **Process**: `Alignment` → `CRE` (BED) → `validated_by_atac` set via ATAC intersect (or False if missing).
3. **Validate**: `CRE` intersect ATAC‑seq (optional) → retain only `validated_by_atac = True` (if ATAC present); otherwise, all are `False`.
4. **Join**: `CRE` + `ExpressionProfile` → `CREAnalysisResult` via mixed model.
5. **Output**: `CREAnalysisResult` → ranked markdown table, PDF report.

## Constraints & Validation Rules

* **Coordinate System**: 0‑based, half‑open (BED standard).
* **FDR Threshold**: `p_value_adj` < 0.05 to be reported as significant.
* **Collinearity**: If `vif_score` > 5, `is_collinear` = True and the CRE‑gene pair is excluded from independent effect testing.
* **Motif Weighting**: `motif_score` is used as a predictor weight; CREs without a motif score receive a default weight of 0.5.
* **Summit Match**: `summit_match_flag` is set only for the top‑10 CREs per stress; the overall percentage is aggregated in the statistical summary (SC‑005).
* **ATAC Validation**: `validated_by_atac` is True only if ATAC data is present and the CRE overlaps a peak. If ATAC is missing, `validated_by_atac` is False for all CREs.
* **Missing Data**: If any required expression variable is absent for a gene, the gene is excluded from modeling (FR‑011).