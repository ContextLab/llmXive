# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Objective
Develop a reproducible end‑to‑end pipeline that (1) builds a high‑threshold co‑expression network from public *Arabidopsis thaliana* (and optionally other plant) RNA‑seq data, (2) maps co‑expressed gene pairs to STRING protein IDs, (3) evaluates recovered edges against a high‑confidence reference set from STRING, (4) provides an independent experimental benchmark, and (5) tests functional coherence via GO enrichment.

## Prior Work & References
- **STRING database** (v11.5) high‑confidence interaction set (combined score ≥ 700). Verified dataset URLs:  
  - `https://huggingface.co/datasets/polinaeterna/test_string_to_dict/resolve/main/data/train-00000-of-00001-3e7bb60eb6e19f8c.parquet` (parquet) – contains `protein1`, `protein2`, `combined_score`.  
  - `https://huggingface.co/datasets/yuanchuan/annotated_reference_strings/resolve/main/en/crossref-part-00001.jsonl.gz` (JSONL) – auxiliary reference.  

- No verified URLs are available for the GEO RNA‑seq series required by FR‑001; the pipeline will download directly from NCBI GEO using the accession identifiers supplied in `config/species.yaml`. This complies with the constitution’s requirement that external datasets be fetched from a canonical source on each run.

## Dataset Strategy

| Dataset | Source (Verified URL) | Access Method | Variables Required |
|---------|----------------------|---------------|--------------------|
| STRING high‑confidence interactions (combined score ≥ 700) | `https://huggingface.co/datasets/polinaeterna/test_string_to_dict/resolve/main/data/train-00000-of-00001-3e7bb60eb6e19f8c.parquet` (parquet) | `datasets.load_dataset("polinaeterna/test_string_to_dict", split="train")` | `protein1`, `protein2`, `combined_score` |
| STRING experimental interactions (evidence = “experimental”) | Same parquet file (filtered on `evidence_type == "experimental"` in code) | Programmatic filter | `protein1`, `protein2`, `combined_score`, `evidence_type` |
| GEO RNA‑seq Count Matrices (per species) | **None verified** – downloaded from NCBI GEO at runtime using accession IDs (e.g., GSEXXXXX) | `code/data/download_gse.py` (uses `requests` + GEOquery) | Raw integer counts matrix, sample metadata, and normalized expression vector |

All downloads are checksum‑verified (`sha256`) and recorded in `data/checksums.yaml` for provenance.

## Methodology Overview
1. **Download** raw count matrices for each species (FR‑001). Abort if < 20 samples (minimum for stable correlation).  
2. **Normalize** counts using TPM or DESeq2 VST (user‑selectable via `--norm-method`).  
3. **Optional batch‑effect correction** via `limma::removeBatchEffect` (`--batch-correct` flag).  
4. **Filter** genes with CPM < 1 in > 80 % of samples before correlation calculation (FR‑003).  
5. **Pre‑select** the top 5 000 most variable genes by median absolute deviation to keep the correlation matrix tractable (addresses memory limits).  
6. **Compute** pairwise correlation (Pearson default, optional Spearman or biweight) and obtain p‑values; apply Benjamini–Hochberg FDR and retain edges with *r* ≥ THRESHOLD (default 0.8, never below).  
7. **Split** the sample set (training/hold‑out) before network construction; the hold‑out set is used only for evaluation, preventing leakage.  
8. **Map** gene identifiers to STRING protein IDs using `org.At.tair.db`; fallback to Ensembl BioMart if needed (FR‑005). Unmapped genes are omitted; warnings logged.  
9. **Evaluation**:  
   - **Primary benchmark** – compare predicted edges to STRING high‑confidence interactions (combined score ≥ 700) and compute AUROC and AUPRC (FR‑006).  
   - **Independent benchmark** – restrict STRING to interactions whose evidence type is *experimental* (no co‑expression evidence) and recompute AUROC/AUPRC. This mitigates circularity because the experimental set is orthogonal to the co‑expression signal.  
   - **Baseline** – generate multiple degree‑preserving random rewiring iterations, compute AUROC/AUPRC for each, and report an empirical p‑value for the observed performance.  
10. **Functional Enrichment**: Run GOATOOLS Fisher’s exact test on the union of genes in the predicted PPIs for each species, apply Benjamini–Hochberg (FDR ≤ 0.05). Report at least one GO term with adjusted p < 0.05, or “No significant enrichment”.  
11. **Performance Benchmark**: Record wall‑clock time via the `make benchmark` target; CI fails if it exceeds **6 hours** (SC‑003).  
12. **Reproducibility**: All stochastic steps respect a global `--seed` flag; `make reproducibility-check` re‑runs the pipeline with the same seed and asserts identical SHA‑256 hashes for `evaluation_metrics.json` and `go_enrichment_<species>.tsv`, thereby satisfying SC‑004.  

## Statistical Rigor
- **Multiple‑testing correction**: Benjamini–Hochberg applied to correlation p‑values before thresholding (addresses FR‑004 methodological gap).  
- **Power considerations**: With ≥ 20 samples, the minimum detectable Pearson correlation at α = 0.05 (two‑tailed) is ≈ 0.44 (Cohen, 1988); we note this limitation in the manuscript.  
- **Correlation assumptions**: Users may select Spearman or biweight mid‑correlation if normality is violated; diagnostics are logged.  
- **Cross‑validation**: The 80/20 split provides a hold‑out evaluation; additional k‑fold CV is optional and documented.  
- **Baseline significance**: Empirical p‑value derived from random‑graph AUROC distribution (see Phase 6).  
- **Circularity mitigation**: By reporting performance on the *experimental* subset of STRING (which excludes co‑expression evidence), we avoid inflating metrics due to overlapping evidence sources.  

## Success‑Criterion Verification Plan
- **SC‑001**: `test_metrics.py` asserts AUROC > 0.70 and AUPRC ≥ 0.65, and baseline empirical p‑value < 0.05 for each species.  
- **SC‑002**: `test_go.py` asserts at least one GO term with adjusted p < 0.05 (or graceful “No significant enrichment”).  
- **SC‑003**: `benchmark` target records wall‑clock time; CI timeout set to 6 h.  
- **SC‑IV**: `reproducibility-check` re‑runs with same seed and compares SHA‑256 hashes of `evaluation_metrics.json` and `go_enrichment_<species>.tsv`; failures abort CI.  
- **SC‑V**: `test_outputs.py` checks presence and parsability of `predicted_ppi_<species>.tsv`, `evaluation_metrics.json`, `go_enrichment_<species>.tsv`, `pipeline.log`.  

All verification steps are encoded as pytest tests and executed in CI (`.github/workflows/ci.yml`).  

--- 
