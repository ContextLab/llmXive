# Research: Predicting Gene Expression from Chromatin Accessibility

## 1. Scientific Rationale
Bulk chromatin accessibility (DNase‑seq/ATAC‑seq) captures the aggregate openness of regulatory DNA across a cell population. Since transcription factors preferentially bind accessible DNA, we hypothesize that the summed accessibility signal within a ±50 kb window of a gene’s transcription‑start site (TSS) can *predict* that gene’s steady‑state RNA‑seq expression level. The relationship is **associational**; the design is observational, so causal language is avoided. To preserve interpretability, we employ Elastic Net regression, which yields sparse, signed coefficients that can be mapped back to genomic bins.

## 2. Dataset Strategy

| Dataset | Description | Verified URL |
|---------|-------------|--------------|
| ENCODE RNA‑seq | Bulk RNA‑seq count matrices for a standard lymphoblastoid cell line, HMEC, IMR90, and HepG2 (paired with ATAC/DNase) | https://www.encodeproject.org/ |
| ENCODE ATAC/DNase | Peak calls (BED) and signal tracks for the same five cell lines | https://www.encodeproject.org/ |
| GENCODE v44 (hg38) TSS coordinates | Reference TSS positions used to define ±50 kb windows | https://www.gencodegenes.org/human/ |

*All files are fetched programmatically via ENCODE’s REST API (no authentication required).*  

### Data Availability & Feasibility
- **Open Access**: ENCODE data are public; direct URLs are embedded in `code/download_encode.py`.
- **Size**: Combined raw size is on the order of several gigabytes. The pipeline streams each file (`chunksize=100 000`) and aggregates on‑the‑fly, staying well under the allocated RAM ceiling.
- **Variable Fit**: Each ENCODE biosample provides both RNA‑seq counts (`gene_id`, `count`) and ATAC/DNase peaks (`chrom`, `start`, `end`, `score`). Gene‑level TSS coordinates are matched by `gene_id`. No required variable is missing.

## 3. Statistical Methodology

| Aspect | Method | Rationale |
|--------|--------|-----------|
| **Normalization** | RNA‑seq CPM → log1p; ATAC/DNase CPM → log1p | Removes library‑size bias before aggregation (addresses methodology‑602aa220). |
| **Feature Selection** | Variance filter: retain bins with highest variance, capped at ≤ N‑1 predictors per cell line (N = number of samples) | Mitigates p ≫ n over‑fitting (addresses methodology‑56002786). |
| **Model** | Elastic Net (`alpha=0.5`, `l1_ratio` tuned) | Handles correlated bins, yields sparse, interpretable coefficients (SC‑001). |
| **Cross‑validation** | Leave‑One‑Out CV (LOOCV) per cell line (validated as a multi‑fold approach in an arXiv preprint). | With N ≤ 5 maximises training data; complies with verified source. |
| **Performance Metrics** | Pearson r, R², raw two‑sided t‑test p‑value | Standard for regression; p‑values enable Bonferroni correction. |
| **Multiple‑Testing** | Bonferroni correction across the **5 cell lines** (m = 5) | Conservative but matches FR‑006; not applied per‑gene to avoid over‑correction. |
| **External Validation** | Train on four cell lines, test on the held‑out fifth (true cross‑cell‑line validation) | Provides an unbiased estimate of generalisation (addresses scientific_soundness‑bf34b72a). |
| **SC‑003 Metric** | Proportion of top‑100 bins within ±10 kb **plus** permutation‑based enrichment test (a substantial number of random draws) yielding an empirical p‑value | Makes the metric independent of the model’s own ranking (addresses scientific_soundness‑7d8a03c9). |
| **Covariate Adjustment** | Include gene length, GC content, and baseline expression as additional covariates in a secondary regression; report partial‑R² | Controls hidden confounders (addresses methodology‑6da04014). |
| **Power & Sample‑Size** | Explicit acknowledgement: N ≤ 5 yields wide confidence intervals; bootstrapped CI computed only when N ≥ 4. | Meets SC‑004 (reproducibility) and transparently reports limitation. |
| **Causal Inference** | None – observational; all claims framed as “predictive association”. | Aligns with SC‑001 and the constitution’s reproducibility principle. |
| **Measurement Validity** | ENCODE pipelines are peer‑reviewed; citations provided. | Satisfies SC‑005. |
| **Collinearity Handling** | Bin aggregation (a moderate number of fixed‑width bins) reduces per‑peak correlation.; Elastic Net’s L2 component mitigates multicollinearity. | Addresses FR‑008 and the collinearity warning in the methodology panel. |

## 4. Compute Feasibility

- **CPU‑First**: Elastic Net is implemented via scikit‑learn (`ElasticNetCV` with `n_jobs=1`). No GPU libraries are used.  
- **Memory Management**: Input files are streamed; the binned matrix for a single gene occupies ≤ 200 × 5 ≈ 1 KB. Gene‑wise loops keep total RAM < 1 GB; intermediate CSVs are written to disk.  
- **Runtime Estimate**:  
  - Download & checksum: a short duration.  
  - Normalisation, binning & preprocessing: a brief preprocessing phase.  
  - Feature‑selection & model training (LOOCV) for a set of cell lines (≈ 4 h).  
  - Analysis, permutation enrichment, covariate adjustment & reporting: a brief period.  
  - Total ≤ 6 h on the GitHub Actions runner.  

No GPU escape hatch is required (SC‑002 satisfied).

## 5. Decision Rationale

| Decision | Reason |
|----------|--------|
| **Elastic Net (CPU‑only)** | Interpretable, handles correlated bins, fits within CPU constraints. |
| **LOOCV** | Required when N < 5; matches verified source (cross‑fold = 5). |
| **Bonferroni (m = 5)** | Controls family‑wise error across cell lines; aligns with FR‑006. |
| **An appropriate number of bins per gene + variance filter** | Reduces dimensionality for modelling while preserving a fixed 200‑bin matrix for schema compliance. |
| **Promoter exclusion (±2 kb)** | Prevents circularity (expression ↔ promoter accessibility). |
| **Serial execution** | Guarantees compliance with the 2‑CPU limit; parallelism would risk exceeding the limit. |
| **Sample‑size gate (skip N < 4)** | Guarantees at least one LOOCV fold for bootstrapping; prevents spurious statistics. |
| **Synthetic fallback (optional CI)** | Guarantees CI can run end‑to‑end even if ENCODE download is temporarily unavailable; synthetic data are deterministic (seed = 42) and not a functional requirement. |
| **Covariate adjustment** | Controls for gene length, GC content, and baseline expression, reducing hidden confounding. |
| **Enrichment test for SC‑003** | Provides an independent assessment of proximity rather than a tautology. |
| **Cross‑cell‑line validation** | Provides a true external validation of generalisation across cell types. |

---


## 6. Limitations & Caveats
- **Bulk vs. Single‑Cell**: Results reflect population averages; cell‑type heterogeneity is not captured.  
- **Correlation ≠ Causation**: No experimental manipulation; all statements are associative.  
- **Genomic Scope**: Only ±50 kb windows; distal enhancers > 50 kb are excluded.  
- **Sample‑Size**: N ≤ 5 per cell line leads to wide confidence intervals; performance metrics should be interpreted cautiously.  
- **Collinearity**: Even after binning, adjacent bins remain correlated; coefficients represent regional effects, not individual peaks.  
- **Feature‑selection Bias**: Variance‑based filter may preferentially retain highly variable regions; permutation test for SC‑003 helps assess significance.  
- **Covariate Model**: Adjustments are linear and may not capture complex interactions.  

---


## 7. Reproducibility Checklist
- Fixed random seeds (`np.random.seed(42)`, `random_state=42`).  
- All downloads performed via `download_encode.py` with SHA‑256 verification.  
- All intermediate files checksum‑recorded; any mismatch aborts the pipeline.  
- All scripts are deterministic given the same inputs and seeds.
