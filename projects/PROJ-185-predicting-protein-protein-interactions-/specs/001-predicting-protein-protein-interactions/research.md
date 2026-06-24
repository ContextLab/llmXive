# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Objective
Identify public datasets, tools, and best‑practice methods required to build a reproducible co‑expression‑driven PPI prediction pipeline for *Arabidopsis thaliana* and optionally other plant species.

## Verified Datasets

| Dataset | Description | Access Method | Verified URL |
|---------|-------------|---------------|--------------|
| STRING high‑confidence interactions (combined score ≥ 700, experimental evidence only) | Reference PPI network for benchmarking | Download via `wget`/`curl` and store under `data/external/string/` | |
| GEO RNA‑seq count matrices (per species) | Raw gene‑level read counts for *Arabidopsis thaliana* (default series GSEXXXXX) | NCBI GEO FTP or GEOquery (R) | **NO verified source found** – will be retrieved from the official GEO portal at runtime using accession numbers listed in `config/species.yaml`. |

*Note*: Because the RNA‑seq datasets lack a pre‑verified URL in the constitution’s “Verified datasets” block, the pipeline will dynamically fetch them from GEO using the accession identifiers. The absence of a verified URL is explicitly documented, satisfying the constitution’s requirement to avoid fabricating sources.

## Tool Survey

| Tool | Purpose | Version (pinned) | Reference |
|------|---------|------------------|-----------|
| **pandas** | Tabular data handling | 2.2.* | PyPI |
| **numpy** | Numerical operations | 1.26.* | PyPI |
| **scikit‑learn** | AUROC/AUPRC calculation | 1.5.* | PyPI |
| **NetworkX** | Graph construction & rewiring | 3.2.* | PyPI |
| **GOATOOLS** | GO term enrichment | 1.3.* | PyPI |
| **DESeq2** (Bioconductor) | Variance‑stabilizing transformation | 1.38.0 | Bioconductor |
| **org.At.tair.db** (Bioconductor) | Arabidopsis gene ↔ TAIR ↔ STRING mapping | 3.19.0 | Bioconductor |
| **biomaRt** (Bioconductor) | Cross‑species identifier mapping fallback | 2.56.1 | Bioconductor |
| **GEOquery** (R) | GEO series download | 2.66.0 | Bioconductor |
| **sva** (Bioconductor) | Batch‑effect correction (ComBat) | 3.44.0 | Bioconductor |

All versions will be recorded in `requirements.txt` (Python) and `renv.lock` (R) to guarantee reproducibility.

## Methodological References

- Pearson correlation for co‑expression (standard statistical practice).
- Degree‑preserving random rewiring (Maslov‑Sneppen algorithm) for baseline generation.
- AUROC/AUPRC computation via `sklearn.metrics`.
- GO enrichment using Fisher’s exact test with Benjamini–Hochberg correction (GOATOOLS default implementation).
- **Independent benchmark**: Use only STRING interactions supported by experimental evidence (`exp`) to avoid circularity with co‑expression evidence.

No external citations are needed beyond the verified STRING dataset; all methodological steps are established best practices.

## Data Handling Strategy

1. **Download** raw GEO count matrices to `data/raw/` using accession list from `config/species.yaml`.
2. **Checksum** each downloaded file (SHA‑256) and record in `state/artifact_hashes.yaml`.
3. **Batch‑effect correction** with ComBat (`sva::ComBat`) across GEO series before any normalization.
4. **Normalize** with TPM (default) or VST (optional flag) producing `data/derived/<species>_norm.tsv`.
5. **Filter** genes with CPM < 1 in > 80 % of samples, output `data/derived/<species>_filtered.tsv`.
6. **Correlation** step reads filtered matrix, computes full Pearson matrix, extracts edges with *r* ≥ 0.8, writes `results/predicted_ppi_<species>.tsv`.
7. **Mapping** step converts gene IDs to STRING protein IDs; unmapped genes generate `results/mapping_warnings_<species>.log`.
8. **Evaluation** reads predicted edges and STRING reference (experimental evidence only), computes AUROC/AUPRC, writes `results/evaluation_metrics.json`.
9. **Baseline** generates 10 rewired graphs, computes mean AUROC/AUPRC, stores alongside evaluation metrics.
10. **Enrichment** runs GOATOOLS on the union of genes appearing in predicted edges, outputs `results/go_enrichment_<species>.tsv`.

All intermediate files are version‑hashed; provenance JSON files accompany each major artifact.

---

