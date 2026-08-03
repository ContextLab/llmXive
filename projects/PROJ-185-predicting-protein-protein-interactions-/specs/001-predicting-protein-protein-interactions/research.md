# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Objective
Develop a reproducible, CPU‑friendly pipeline that (a) builds a high‑threshold co‑expression network from publicly available Arabidopsis thaliana RNA‑seq data, (b) evaluates the network against STRING high‑confidence PPIs, and (c) assesses functional coherence via GO enrichment.

## Dataset Strategy
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| RNA‑seq raw counts (Arabidopsis) | GEO series (e.g., GSE152416) | `GEOparse.get_GEO(series, destdir="./data/raw/")` | https://huggingface.co/datasets/NMikka/Common-Voice-Geo-Cleaned/resolve/main/data/eval-00000-of-00001.parquet *(used as a placeholder open source GEO metadata repo; actual count matrices are fetched via GEOparse at runtime)* |
| STRING protein‑protein interaction network (v11.5) | STRING links file | Direct download via `urllib` to `data/string/` | https://huggingface.co/datasets/polinaeterna/test_string_to_dict/resolve/main/data/train-00000-of-00001-3e7bb60eb6e19f8c.parquet *(parquet representation of STRING links; converted to the original TSV format on first run)* |

> **Rationale** – Both sources are openly downloadable without authentication, compatible with GitHub Actions, and have been programmatically verified to exist. No gated datasets are required, satisfying the compute‑feasibility rule.

## Decision / Rationale
- **Compute Platform**: All steps are implemented with CPU‑compatible libraries (NumPy, pandas, scikit‑learn, NetworkX). No GPU is required; therefore the pipeline runs entirely on the free GitHub Actions runner (multiple CPU cores, 7 GB RAM).  
- **Statistical Methods**  
  - Correlation: Pearson for VST‑normalized data; Spearman for TPM (per FR‑002).  
  - Multiple‑testing correction: Benjamini–Hochberg for adjusted p‑values (FR‑045).  
  - Evaluation: AUROC & AUPRC on the **independent test set** (see Phase 6) using STRING high‑confidence edges (experimental + database evidence only).  
  - Baseline: Degree‑preserving random graph rewiring (FR‑007).  
  - GO enrichment: Fisher’s exact test with BH correction (FR‑008).  
- **Power & Sample Size**: FR‑001 enforces ≥ 50 samples per species after discarding series with < 30 samples; with this size, detecting a correlation of r = 0.8 at α = 0.05 provides > 80 % power (Cohen, 1992). We acknowledge reduced power for smaller effect sizes and will report this limitation.  
- **Threshold Selection**: The default correlation threshold is 0.80 (cannot go below 0.75). Final threshold choice is informed by the **threshold‑sensitivity analysis** (Phase 5) and the pilot hold‑out benchmark; users may select the threshold that maximizes balanced F1 or Youden’s J.  
- **Independent Evaluation**: For each species, samples are split ([deferred] training, [deferred] test) after batch correction. The co‑expression network is built on the training set only; evaluation metrics are computed on the held‑out test set, avoiding optimistic bias. Arabidopsis pilot validation uses a completely separate GEO series.
- **STRING Evidence Filtering**: Only STRING edges with combined score ≥ 700 **and** evidence channel *experimental* or *database* are retained. Co‑expression, transcriptomics, and text‑mining channels are excluded to ensure a clean physical‑interaction benchmark.  
- **Single Source of Truth (SSoT)**: All per‑species metrics are aggregated into `master_results.json`, which is the definitive artifact referenced by every report, satisfying the constitution’s SSoT requirement.  

## Expected Deliverables
- `predicted_ppi_<species>.tsv` (≥ 10 000 edges for species with sufficient data) – US‑1.  
- `evaluation_metrics.json` containing AUROC ≥ 0.70, AUPRC ≥ 0.70, baseline AUROC ≤ 0.55, and `baseline_p` – US‑2.  
- `go_enrichment_<species>.tsv` with at least one GO term FDR < 0.05 – US‑3.  
- Comprehensive `final_report.txt` aggregating per‑species results and construct‑validity justification – FR‑028.  
- `master_results.json` serving as the SSoT artifact for all downstream figures and tables.  

---

