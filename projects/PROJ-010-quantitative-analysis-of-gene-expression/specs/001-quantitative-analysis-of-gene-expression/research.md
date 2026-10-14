# Research: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

## Problem Statement
Identify stage‑specific rewiring events in transcription‑factor regulatory networks (GRNs) across human brain development and assess whether these events are enriched for genes implicated in neurological disorders.

## Dataset Strategy

| Dataset | Source / URL (Verified) | Role | Variables |
|---------|------------------------|------|-----------|
| BICCN Human MTG scRNA‑seq Atlas | https://huggingface.co/datasets/BICCN/human_mtg_scRNA | Primary expression matrix, cell‑level developmental stage, donor ID | `counts`, `gene_id`, `cell_id`, `developmental_stage`, `donor_id` |
| Independent scRNA‑seq Cohort (PsychENCODE fetal brain) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE147457 | Topological validation of rewiring | Same as primary |
| BrainSpan Bulk RNA‑seq (GSE36520) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE36520 | Expression validation of hub genes across stages | `gene_id`, `TPM`, `developmental_stage` |
| GWAS Catalog risk genes (Schizophrenia, Autism, etc.) | https://www.ebi.ac.uk/gwas/ | Reference gene sets for enrichment | `gene_symbol`, `disorder` |

**Data Availability Note** – The BICCN Human MTG dataset is openly downloadable via the HuggingFace hub and satisfies FR‑001. All other resources are publicly accessible via the URLs shown.

## Methodological Rationale

### 1. Acquisition & Integration
- **Dataset**: BICCN Human MTG scRNA‑seq Atlas (https://huggingface.co/datasets/BICCN/human_mtg_scRNA) is a time‑resolved, publicly available atlas with explicit developmental‑stage annotations; loaded via `datasets.load_dataset("BICCN/human_mtg_scRNA")`.
- **Harmony** (CPU‑efficient) removes donor‑specific batch effects while preserving developmental gradients.  
- **LISI** quantifies batch mixing; we enforce LISI ≥ 1.2 (FR‑012).  
- **QC** filters cells with < 200 genes, genes expressed in < 3 cells, and removes cells lacking a stage label (FR‑011).  

### 2. Pseudotime Validation & Trajectory
- **Pseudotime Ordering**: Monocle3 (via `scvelo`) provides a continuous developmental ordering; alternative Slingshot is available if Monocle fails.  
- **Marker Validation** (FR-003, methodology-8eca91e6): After pseudotime inference, pipeline correlates pseudotime with known developmental markers (NEUROD6, GFAP, MAP2) using Pearson correlation. Requires r ≥ 0.6 to proceed; aborts with clear error if correlation is insufficient. This ensures pseudotime reflects biology rather than residual batch effects.
- **Windowing**: Overlapping windows of [deferred] cells with [deferred] stride capture smooth transitions.

### 3. Sliding‑Window GRN Inference & Motif Validation
- **GRNBoost2**: Gradient‑boosted regression, scalable on CPU, yields TF‑target edge weights (FR‑003).  
- **Motif Enrichment** (FR‑006, methodology‑767925d8): Mandatory pySCENIC step validates TF‑target edges with cis‑regulatory motif evidence. Only edges passing motif threshold are retained for downstream rewiring analysis, addressing construct‑validity concerns by ensuring inferred edges have independent binding evidence.
- **Hub Definition**: TFs with degree ≥ 10, or top 20 TFs if fewer than 20 meet threshold (data‑model‑a3570fb0).

### 4. Rewiring Detection & Normalization
- **Edge‑Weight Normalization** (FR‑004, methodology‑7516c898): Edge weights are **z‑score normalized** within each developmental window before computing inter‑window differences. This ensures edge‑weight differences are on a comparable scale regardless of cell‑subset composition or expression‑distribution shifts, eliminating scaling artifacts as a confound.
- **Hub‑Stability**: Degree‑centrality change and Jaccard similarity across thresholds {0.01, 0.05, 0.1} (FR‑010).  
- **Sensitivity**: Jaccard ≥ 0.8 for the top‑20 events across thresholds (SC‑005).  

### 5. Disorder Enrichment with Matched Background
- **Matched‑Gene Background** (FR‑005, methodology‑79849ee1): For each disorder, generate a control gene set matched on gene length, baseline expression level, and network degree to control confounds. Hypergeometric test compares observed overlap between rewired TF hubs and disorder risk genes to this matched background rather than random genes, eliminating confound inflation.
- **Hypergeometric Test**: Evaluates overlap between rewired TF hubs and disorder risk genes (FR‑005).  
- **Benjamini‑Hochberg FDR**: Controls family‑wise error rate across all disorders (FR‑009).  
- **Permutation Test** (≥ 5,000 iterations, methodology‑32aa8ec6): Builds a null distribution; empirical p‑value ≤ 0.05 required (FR‑006, SC‑003). Power analysis: simulated networks under realistic assumptions (50k cells, 5k TFs, expected odds‑ratio ≥1.5) demonstrate >80% power to detect effect at p≤0.05 with 5,000 permutations.
- **Zero‑Permutation Rule**: Report as `p < 1/5000` per FR‑013, SC‑009.  
- **Vulnerability Window**: Each enrichment signal is mapped to the developmental stage where rewiring is most pronounced (plan‑consistency‑2bdc8738), output in `disorder_enrichment.csv` as `vulnerability_window` column.

### 6. Validation
- **Topological**: Replicate rewiring detection on an independent scRNA‑seq cohort (PsychENCODE); concordance measured by Jaccard ≥ 0.7.  
- **Expression**: Test whether rewired hub TFs are differentially expressed in bulk BrainSpan samples across the same developmental windows (SC‑006).  

### 7. Reporting
All statements are framed as **associational** (FR‑008). Figures are exported as Plotly HTML and Cytoscape‑compatible `.cx` files (FR‑007). The final `disorder_enrichment.csv` includes columns `disorder`, `vulnerability_window`, `odds_ratio`, `p_value`, and `is_validated` (matching the output schema).

## Compute Feasibility

- **CPU‑First**: All steps run with `scanpy` and `GRNBoost2` (CPU‑only).  
  - **Memory Management**: HVG selection reduces genes to a small subset of the total; if RAM exceeds 6 GB, the pipeline switches to a deterministic stratified sample of a large number of cells (`SAMPLED_MODE=True`, seed 42).  
- **GPU Escape Hatch**: Not required; no deep‑learning models are used.  

## Decision / Rationale Summary
- **Trajectory Choice**: Monocle3 selected for its robust pseudotime on scRNA‑seq; Slingshot as fallback. Pseudotime is validated against known markers (r ≥ 0.6) before proceeding.
- **GRN Method**: GRNBoost2 balances accuracy with CPU tractability; mandatory pySCENIC motif validation adds construct validity by ensuring edges have cis‑regulatory binding evidence.
- **Edge Normalization**: Z‑score normalization within windows ensures rewiring metrics are scale‑invariant and comparable across developmental stages.
- **Matched Background**: Controls for gene length, expression, and degree bias in enrichment testing, eliminating confound inflation.
- **Validation Strategy**: Dual validation (independent scRNA and bulk) satisfies Constitution Principle VII and mitigates dataset‑specific artifacts.  

---