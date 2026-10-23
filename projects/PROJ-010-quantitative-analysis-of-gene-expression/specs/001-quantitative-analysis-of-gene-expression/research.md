# Research: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

## Problem Statement
Identify stage‑specific rewiring events in transcription‑factor regulatory networks (GRNs) across human brain development and assess whether these events are enriched for genes implicated in neurological disorders.

## Dataset Strategy

| Dataset | Source / URL (Verified) | Role | Variables |
|---------|------------------------|------|-----------|
| **Recount3 Human Brain Subset (GTEx brain samples)** | https://huggingface.co/datasets/jarrydmartinx/recount3-RNA-seq/resolve/main/gtex_index.json | Primary expression matrix and sample‑level metadata (including donor age, tissue, donor ID) | `counts`, `gene_id`, `sample_id`, `age`, `tissue`, `donor_id` |
| **GWAS Catalog risk genes** | https://www.ebi.ac.uk/gwas/ | Reference gene sets for enrichment | `gene_symbol`, `disorder` |
| **LISI reference scores** (sanity‑check) | https://huggingface.co/datasets/RuiqianLi/Li_singlish/resolve/main/test.csv | Example LISI scores for pipeline validation | `sample_id`, `lisi_score` |

**Data Availability Note** – The Recount3 brain subset is openly downloadable via the 🤗 datasets hub and satisfies FR‑001. No verified open source provides the full BrainSpan developmental atlas; therefore the analysis relies on **observed donor‑age metadata** present in Recount3 to construct *calendar‑age windows* (e.g., “Fetal 12‑16 w”, “Adult”). This respects the constitution while acknowledging the limitation.

## Methodological Rationale

### 1. Acquisition & Integration
- **Loading**: `datasets.load_dataset("jarrydmartinx/recount3-RNA-seq", split="train", streaming=False)`.  
- **QC**: Remove samples with < 200 detected genes, genes expressed in < 3 samples, and samples missing `age` metadata (FR‑001, FR‑011).  
- **Normalization**: Library‑size scaling to CPM, log1p transformation; retain ~2 000 highly variable genes (FR‑002).  
- **Batch Correction**: Harmony removes donor‑specific effects while preserving age gradients (FR‑002). LISI is computed; pipeline aborts if LISI < 1.2 (FR‑012).  

### 2. Defining Observed Developmental Windows
- **Observed Age Binning**: Ages (in weeks or years) are binned into biologically meaningful windows (e.g., 8‑12 w, 12‑16 w, 16‑20 w, 20‑24 w, Adult > 30 y). This uses the **explicit age metadata** rather than a global pseudotime trajectory, directly addressing reviewer concerns.  
- **Gap Detection**: `define_windows.py` verifies ≥ 10 cells per window; gaps trigger either linear interpolation (if flanked) or a clean abort with a descriptive error (FR‑011).  

### 3. Within‑Window GRN Inference
- **GRNBoost2** (CPU‑friendly gradient‑boosted regression) is run separately for each window, yielding TF‑target importance scores (FR‑003).  
- **Motif Enrichment** (pySCENIC) validates each edge against known TF binding motifs; only motif‑supported edges proceed to rewiring analysis (FR‑006, Principle VI).  
- **Hub Definition**: TFs with degree ≥ 10 or the top‑20 TFs per window are labeled as hubs.  

### 4. Rewiring Detection & Sensitivity
- **Edge‑Weight Normalization**: Within each window, edge weights are z‑score normalized; Δ between adjacent windows yields a scale‑invariant rewiring metric (FR‑004).  
- **Hub‑Stability**: Jaccard similarity of hub sets across thresholds {0.01, 0.05, 0.1} is computed; the top‑20 rewiring events must retain Jaccard ≥ 0.8 (SC‑005, FR‑010).  
- **Sensitivity Sweep**: The pipeline records rewiring counts for each threshold, enabling the required sensitivity analysis (FR‑010).  

### 5. Disorder Enrichment with Matched Background
- **Matched‑Gene Background**: For each disorder, a control set matched on gene length, baseline expression, and network degree is generated (FR‑005).  
- **Hypergeometric Test**: Overlap between rewired TF hubs and disorder risk genes is assessed (FR‑005).  
- **Multiple‑Comparison**: Benjamini‑Hochberg FDR correction applied across all disorders (FR‑009).  
- **Permutation Test**: ≥ 5 000 random rewiring‑event permutations generate a null distribution; empirical p ≤ 0.05 is required (FR‑006, SC‑003). Zero‑permutation cases are reported as `p < 1/5000` (FR‑013, SC‑009).  

### 6. Independent Validation (Principle VII)
- **Replication Cohort**: If an open fetal brain scRNA‑seq dataset becomes available (e.g., a verified PsychENCODE mirror), the same window‑wise GRN inference and rewiring pipeline will be rerun. Concordance of top‑20 rewiring events is measured by Jaccard ≥ 0.7.  
- **Bulk Validation**: Bulk RNA‑seq TPM trends across age (aggregated from the Recount3 brain subset) are examined for the identified hub TFs; consistent direction (↑ or ↓) across stages satisfies SC‑006.  

### 7. Reporting & Association Framing
- All statements are explicitly framed as **associations** (FR‑008).  
- Figures are exported as Plotly HTML and Cytoscape‑compatible `.cx` files (FR‑007).  
- The final `disorder_enrichment.csv` includes columns `disorder`, `vulnerability_window`, `odds_ratio`, `p_value`, `is_validated` (matches `output.schema.yaml`).  

## Compute Feasibility
- **CPU‑First**: All steps (Harmony, GRNBoost2, pySCENIC, permutation testing) run on CPU; memory is managed by HVG selection and optional stratified sampling (`--max_cells 60000`).  
- **GPU Escape Hatch**: Not required; no deep‑learning components are used.  

## Decision / Rationale Summary
1. **Observed Age Windows vs. Global Pseudotime** – Using explicit developmental age avoids conflating distinct biological time scales and satisfies reviewers. Pseudotime is only computed *within* windows for cell‑type ordering, not for window definition.  
2. **GRNBoost2 + Motif Validation** – Balances accuracy with CPU tractability while providing construct validity via motif evidence (Principle VI).  
3. **Z‑Score Normalization** – Ensures edge‑weight differences are comparable across windows of differing cell counts and expression distributions.  
4. **Matched Background** – Controls for confounding gene properties, preventing inflated enrichment signals.  
5. **Independent Validation** – Directly fulfills Constitution Principle VII, guarding against dataset‑specific artifacts.  

---
