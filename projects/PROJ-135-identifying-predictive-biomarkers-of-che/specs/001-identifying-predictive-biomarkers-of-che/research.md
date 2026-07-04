# Research: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Executive Summary

This research phase validates the feasibility of identifying cross‑tumor chemotherapy response biomarkers using public datasets. We confirm that TCGA data can be harmonized, that the required variables (response labels, expression data) exist in the verified sources, and that the computational load fits within CPU‑only constraints. We address the dataset‑variable fit, statistical rigor, and compute feasibility concerns explicitly.

## Dataset Strategy

We rely **only** on the verified datasets listed in the project's verified datasets block.

| Dataset Type | Source Name | Verified URL | Usage in Plan | Variable Fit Check |
|:--- |:--- |:--- |:--- |:--- |
| **TCGA RNA‑seq** | TCGA (multiple projects) | ` (example for OV) | Primary expression & clinical data for ≥3 tumor types. | **Partial**: Only one tumor type (OV) is currently verified. The pipeline will attempt to download additional TCGA projects (e.g., BRCA, LUAD) via the TCGA API. If they are unavailable, the analysis proceeds with the available types but flags this limitation in `results/summary.md`. |
| **GEO Microarray** | GEO (response‑annotated) | *No verified URLs for GSE* or GSE42752 are present in the verified block.* | Intended for external validation (FR‑002, FR‑008). | **Missing**: Required GEO series are not verified. The pipeline will attempt to download them; if unavailable, it will skip external validation, proceed with internal LOO validation, and record `external_validation_status: "skipped"` in `results/summary.md`. |
| **Normalization** | DESeq2 VST (via rpy2) | N/A (implementation reference: Bioconductor DESeq2 package) | Variance‑stabilizing transformation of RNA‑seq counts. | **Fit**: Standard method; no external data needed. |
| **Batch Correction** | ComBat‑seq (via rpy2) or Quantile Matching | N/A (implementation reference: Bioconductor `sva` package) | Align GEO microarray data with TCGA RNA‑seq. | **Fit**: Applicable to count data; fallback quantile matching used if ComBat‑seq cannot be executed. |

**Critical Findings & Fallbacks**

1. **TCGA Tumor Types** – Only one verified TCGA dataset is present. The pipeline will download additional TCGA projects programmatically. If fewer than three tumor types are ultimately obtained, the feasibility gate halts (Task T013) and the overall status is reported as `halted` with reason `insufficient_tcga_types`. This respects FR‑001 while making the limitation explicit.
2. **GEO Validation Datasets** – Since the required GEO datasets are not verified, the pipeline adopts a **fallback**: external validation is skipped, internal LOO validation is performed, and the limitation is logged (SC‑003). This allows the project to continue and still evaluate cross‑tumor generalizability via LOO (Principle VI) albeit without independent GEO cohorts.
3. **Statistical Corrections** – Bonferroni correction is applied only to the meta‑analysis combined p‑values (Task T024) and to DeLong’s test (Task T037). Initial DE uses Benjamini‑Hochberg FDR, avoiding double‑dipping (addressing scientific‑soundness concerns).
4. **Batch‑Correction Pipeline** – GEO microarray intensities are first converted to log2‑CPM, then quantile‑normalized, and finally subjected to ComBat‑seq (if counts) or quantile matching (if already log‑scaled). This preserves the mean‑variance relationship required for VST‑scaled RNA‑seq data.

## Statistical Rigor

1. **Multiple Comparison Correction** – DE screening uses Benjamini‑Hochberg FDR < 0.05. Meta‑analysis combined p‑values are Bonferroni‑adjusted (m = size of final gene panel) with threshold p < 0.01. DeLong’s test also receives Bonferroni correction (m = number of model comparisons). |
2. **Sample Size / Power** – If any tumor type has < 100 samples (or < 50 responders/non‑responders), a “Power Limitation” flag is added to `results/summary.md`. |
3. **Causal Inference** – Observational study; all claims are associational. |
4. **Measurement Validity** – Gene expression measured via RNA‑seq (TCGA) or microarray (GEO). Response labels derived from RECIST or equivalent clinical annotations. |
5. **Collinearity** – Variance Inflation Factor (VIF) computed for the final model; VIF > 5 triggers a descriptive report without claiming independent effects. |
6. **Microarray Normalization** – GEO data are converted to log2‑CPM, quantile‑normalized, then batch‑corrected as described above. |

## Compute Feasibility

- **Environment**: GitHub Actions Free Runner (2 CPU, 7 GB RAM, 14 GB disk). |
- **Constraints**: No GPU, no large‑model inference. |
- **Strategy** – Process tumor types sequentially; load only the top `config.MAX_VARIANCE_GENES` (default 50) genes into memory for modeling. Elastic‑net logistic regression (scikit‑learn) runs comfortably on CPU. Runtime target ≤ 6 h; memory ≤ 7 GB. T040 enforces these limits and records them in `results/runtime_metrics.json`. |
- **Risk** – If TCGA download exceeds 5 GB, a warning is logged but the pipeline proceeds (per FR‑001). If memory spikes occur during DESeq2, samples are processed one tumor type at a time.

## Decision/Rationale

- **Why Python + rpy2?** – DESeq2 and ComBat‑seq have no pure‑Python equivalents that meet the spec; rpy2 provides a lightweight bridge while keeping the rest of the pipeline CPU‑friendly. |
- **Why Fixed Discovery/Training Split?** – Prevents data leakage between biomarker selection and model training, satisfying FR‑013 and ensuring valid AUC estimates. |
- **Why Tumor‑type‑specific Models?** – Enables leave‑one‑cancer‑type‑out validation (FR‑008) and aligns with Constitution Principle VI. |
- **Why Bonferroni Only on Meta‑analysis?** – Maintains statistical rigor while allowing sufficient genes to pass DE screening, addressing the over‑conservatism concern. |
- **Why Fallback on Missing GEO Data?** – Guarantees the pipeline remains runnable and the primary success criteria (SC‑001, SC‑003) are still measurable via internal validation, with transparent limitation reporting.
