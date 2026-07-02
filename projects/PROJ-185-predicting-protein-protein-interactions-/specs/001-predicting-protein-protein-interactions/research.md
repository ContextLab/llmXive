# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Feature**: `PROJ-185-predict-ppi-coexpression`  
**Date**: 2026‑07‑01

## Objective
Develop a reproducible, CPU‑only pipeline that transforms publicly available *Arabidopsis thaliana* (and optionally other plant) RNA‑seq datasets into a high‑threshold co‑expression network, maps genes to STRING protein identifiers, and quantitatively evaluates whether the resulting edges recover known physical interactions. Functional relevance is assessed via GO enrichment.

## Construct‑Validity Disclaimer
High‑threshold co‑expression (r ≥ 0.8) is employed as an *associational* proxy for physical protein‑protein interactions, following evidence from Zhang et al., Nat Commun. 2020. The pipeline generates hypothesis‑sets of PPIs; it does **not** claim definitive binding evidence. All claims are framed as associations, and limitations of correlation‑based inference are explicitly discussed in the manuscript.

## Dataset Strategy
| Role | Source | Access Method | Variables Required |
|------|--------|---------------|--------------------|
| RNA‑seq counts | NCBI GEO (e.g., series listed in `config/species_config.yaml`) | `datasets.load_dataset("geo", ...)` via GEOparse (Python) | Raw read counts per gene, sample metadata (tissue, developmental stage, condition) |
| STRING reference | STRING v11.5 (`protein.links.v11.5.txt.gz`) | Direct download from `https://string-db.org` (official release page) | `protein1`, `protein2`, `combined_score`, `evidence_channels` |
| GO ontology | Gene Ontology release 2023‑12‑01 | `goatools` auto‑download | GO term IDs, definitions, hierarchical structure |

*No verified dataset URLs were supplied in the “# Verified datasets” block; therefore the pipeline uses canonical programmatic loaders (GEOparse for GEO, official STRING download page, and GOATOOLS’ built‑in ontology fetcher). All URLs are hard‑coded to the official sources to guarantee reproducibility.*

## Modeling & Statistical Choices
1. **Normalization** – Users choose TPM (fast, pure‑Python) or DESeq2 VST (R, variance‑stabilizing). TPM values are **log2‑transformed** (`log2(TPM + 1)`) before correlation to mitigate compositional effects. VST is the default because it produces data suited to linear correlation (FR‑002). **Caution**: TPM is compositional; Pearson correlation on TPM‑scaled data can induce spurious associations. If TPM is selected, the pipeline logs a warning and recommends using Spearman correlation.
2. **Filtering** – CPM < 1 in > 80 % samples is removed to reduce noise (FR‑003).  
3. **Batch & Covariate Adjustment** –  
   - If > 1 GEO series per species → ComBat (sva) or limma `removeBatchEffect`.  
   - If metadata columns (tissue, stage, condition) exist → linear regression of each gene on covariates; residuals are used for correlation (FR‑022).  
   - **If metadata are absent** → surrogate hidden‑batch correction via PCA on the expression matrix (logged as a warning).  
4. **Correlation** – Pairwise Pearson (mandatory) and optional Spearman (CLI flag). Pearson is the primary metric because the high‑threshold (r ≥ 0.8) has been empirically linked to physical interactions (Zhang et al., Nat Commun. 2020).  
   - **Edge‑selection threshold**: *r ≥ 0.8* (never below, per FR‑004).  
   - **Sensitivity analysis**: thresholds 0.75, 0.80, 0.85 are evaluated **only on raw correlation scores** for performance assessment; edge generation remains at 0.8, preserving FR‑004.  
   - **Multiple testing**: Not required for edge selection (threshold pre‑specified), but for GO enrichment we apply Benjamini–Hochberg FDR (SC‑002).  
   - **Bootstrap CI** (optional) uses 200 resamples of the expression matrix for the top 10 000 edges to obtain 95 % confidence intervals (FR‑015). Edges whose CI does not include the threshold are flagged as non‑robust.  
5. **Evaluation** –  
   - **Positive set**: STRING high‑confidence interactions (combined_score ≥ 700) *excluding* the co‑expression evidence channel.  
   - **Negative set**: A *balanced* random gene‑pair sample equal in size to the positive set (or up to 10 × if positives are very few) to mitigate class‑imbalance bias.  
   - **Metrics**: AUROC, AUPRC computed on *all* raw correlation scores (FR‑020) via scikit‑learn’s `roc_auc_score` and `average_precision_score`. 95 % CIs are obtained by bootstrapping the evaluation set (200 resamples).  
   - **Baseline**: Degree‑preserving random rewiring (10 000 swaps per iteration) generates a null AUROC/AUPRC distribution; a one‑sample Kolmogorov‑Smirnov test yields `baseline_p` (FR‑007, FR‑018).  
   - **Power / Sample‑size**: Assumption of ≥ 50 samples per species gives > 80 % power to detect a true Pearson correlation of 0.8 at α = 0.05 (Cohen, 1992) – documented in the assumptions section.  
6. **Threshold Sensitivity** – Evaluate at r = 0.75, 0.80, 0.85 **only for performance metrics**, not for edge generation; results stored in `threshold_sensitivity_<species>.tsv`. Edge generation remains at 0.8, satisfying FR‑004.  
7. **GO Enrichment** – GOATOOLS performs Fisher’s exact test on the gene set participating in predicted PPIs versus the filtered‑gene universe; Benjamini–Hochberg correction applied (FR‑008). At least one term must reach adjusted p < 0.05 (SC‑002).  

## Reproducibility & Provenance
- **Random Seed**: Global `--seed` flag propagated to NumPy, Python `random`, and R RNGs. All stochastic steps (bootstrap, random baseline, negative sampling) are deterministic given the seed (FR‑012).  
- **Version Pinning**: All Python packages listed in `requirements.txt` with exact versions; R packages installed via `BiocManager::install(version = "3.18")`.  
- **Checksums**: After each download, an SHA‑256 checksum is computed and stored in `state/artifact_hashes.yaml`.  
- **Provenance Log**: Every script writes a JSON line to `pipeline.log` with timestamp, step name, input file hashes, output file hashes, and any warnings (FR‑010).  
- **Schema Validation**: Edge lists validated against `contracts/predicted_ppi.schema.yaml`; raw correlations against `contracts/raw_correlations.schema.yaml`; evaluation JSON against `contracts/evaluation.schema.yaml`; GO enrichment TSV against `contracts/go_enrichment.schema.yaml`; threshold sensitivity TSV against `contracts/threshold_sensitivity.schema.yaml`; pipeline log against `contracts/pipeline_log.schema.yaml`. Pipeline aborts on any schema violation (FR‑013, FR‑019).  

## Compute Feasibility on GitHub Actions
- **Memory**: Gene‑gene correlation matrix is computed in blocks (e.g., 5 000 × 5 000 chunks) to keep peak RAM ≤ 5 GB.  
- **CPU**: All heavy loops are vectorised; optional Numba JIT for speed.  
- **Runtime Estimate**:  
  - GEO download & QC: a brief, network‑bound duration.  
  - Normalization & filtering: a brief processing step.  
 - Correlation (full matrix for ≤ 5 000 genes): [deferred].
  - Bootstrap (optional) + baseline rewiring: ≤ 60 min.  
  - Evaluation & GO enrichment: ≤ 30 min.  
  - Summary & verification: ≤ 10 min.  
  Total ≈ a few hours, well under the prescribed ceiling (SC‑003).  
- **No GPU**: All libraries used have pure‑CPU wheels; `torch` is **not** required.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient samples (< 50) after merging series | Pipeline abort (FR‑024) | Pre‑run sample count check; abort early with clear error. |
| Missing covariate metadata | Covariate adjustment skipped (no‑op) | Apply surrogate PCA‑based hidden‑batch correction; log warning. |
| Gene‑to‑STRING mapping failures | Unmapped genes omitted, warning logged (FR‑005) | Record unmapped IDs; continue with mapped subset. |
| High memory usage for large gene sets | Job OOM | Chunked correlation; limit to top‑most‑variable set of genes as needed (documented). |
| STRING file corruption | Abort with explicit error (FR‑006) | Verify MD5 checksum after download; abort on mismatch. |
| Imbalanced evaluation set | Inflated AUROC/AUPRC | Use balanced negative sampling (equal to positives, up to 10×) and report class‑balance statistics. |
| TPM compositional bias | Spurious correlations | Default to VST; if TPM chosen, log caution and apply log2‑transform; document limitation. |

---



