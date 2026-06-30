# Research: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

## Overview

This research component outlines the data sources, methodological rationale, and statistical strategies required to **identify cis‑regulatory elements (CREs) whose activity is *associated* with stress‑specific transcriptional responses** in *Saccharomyces cerevisiae*. All claims are explicitly framed as *associational*; no causal inference is asserted without orthogonal perturbation data. The term "drive" in the research question is interpreted as "statistically predicts" in the context of observational data.

## Dataset Strategy

The analysis relies on three primary data types:

| Requirement | Dataset Description | Verified Source | Status |
|---|---|---|---|
| **ChIP‑seq (Hsf1, Msn2/4, Hog1)** | Raw FASTQ for each TF‑condition pair (control + three stresses). | **NO verified source found** (spec references GEO GSE####). | **Fatal Gap** – pipeline requires user-supplied data; synthetic data for CI only. |
| **eQTL with stress‑specific fold‑changes** | 1002 Yeast Genomes eQTL summary statistics including effect sizes and log₂FC for heat‑shock, osmotic, oxidative stress. | **NO verified source found**. | **Fatal Gap** – pipeline requires user-supplied data; synthetic data for CI only. |
| **ATAC‑seq (independent validation)** | Genome‑wide chromatin accessibility peaks for yeast under comparable conditions. | **NO verified source found**. | **Deferred** – if missing, pipeline runs in "ATAC-Deferred Mode" and flags results as unvalidated. |
| **General GEO metadata** | Metadata for searching GEO series. | `https://huggingface.co/datasets/cyborvirtue/Geoaux/resolve/main/metadata.jsonl` | **Use** – for metadata lookup only. |

### Dataset Variable Fit

The required variables are:

* Predictor: **ΔPeakSignal** (stress – control ChIP‑seq signal per CRE).
* Outcome: **log2FC** for each gene under each stress (from eQTL).
* Covariate: **PromoterBinding** (baseline TF binding).

Because the verified list lacks the exact yeast ChIP‑seq and eQTL files, **the pipeline distinguishes two modes**:

1. **Real‑Data Mode** – Users must place the required FASTQs and eQTL CSV in `data/raw/` and `data/external/`. The pipeline validates presence of all columns (FR‑011). If ATAC is missing, it runs in "ATAC-Deferred Mode".
2. **Synthetic‑Data Mode** (`--generate-synthetic`) – Generates mock FASTQs and a synthetic eQTL table that conform to `contracts/dataset.schema.yaml`. This mode validates pipeline logic but **does not support biological conclusions**; limitations are reported in the final PDF.
3. **Null‑Synthetic Mode** (`--null-synthetic`) – Generates mock data with **zero correlation** between ΔPeakSignal and log2FC to validate false-positive control.

## Methodological Rationale

### 1. Peak Calling & Sensitivity Sweep (FR‑003)
* **MACS2** at stringent FDR = 0.01 plus a sweep at 0.05 and 0.10.
* **Why**: Yeast genomes are compact; stringent FDR reduces false positives. The sweep quantifies robustness; overlap of top‑20 CREs across thresholds (SC‑004) is reported even when the sampled set is smaller (fallback to available CREs).

### 2. Linear Mixed Model (FR‑005)
* **Model**: `Y_g = β0 + β1·ΔPeakSignal + β2·PromoterBinding + (1|gene) + ε_g`
* **Interpretation**: Tests *association* between CRE signal and gene‑level expression change, controlling for promoter binding. **No causal claim is made.**
* **Assumptions**: Observational; no causality implied. Random intercept captures gene‑specific baseline variance.

### 3. Measurement‑Error Correction (Addressing d21a0091)
* **SIMEX** (Simulation‑Extrapolation) is applied to `ΔPeakSignal` before fitting the LMM to correct attenuation bias caused by noisy ChIP‑seq measurements.
* **Error Estimation**: If technical replicates are missing, a **Poisson noise model** based on sequencing depth is used to estimate measurement error variance, rather than empirical signal variance.
* Outputs: `measurement_error_variance` and `simex_corrected_beta` stored in the results schema.

### 4. Collinearity & Weighting (Addressing c529a358)
* **VIF** > 5 triggers exclusion (FR‑012).  
* **Motif‑score weighting**: distal CREs receive a weight proportional to TF‑motif match confidence, reducing noise from weakly supported CREs.
* **Collinearity Warning**: If PromoterBinding and ΔPeakSignal are highly correlated, the CRE is flagged as "Collinear" and excluded from independent effect testing.

### 5. Permutation Testing (FR‑006)
* 10 000 shuffles of `ΔPeakSignal` (or 1 000 in CI mode) generate an empirical null for β₁; the empirical p‑value is reported.

### 6. Independent ATAC Validation (FR‑013)
* **ATAC-Deferred Mode**: If ATAC-seq data is missing, the pipeline does not abort. Instead, it sets `validated_by_atac = False` for all CREs and flags the final report as "Associational Only (ATAC Deferred)".
* **ATAC-Validated Mode**: If ATAC data is present, CREs lacking ATAC support are excluded.

### 7. Summit‑Match Verification (SC‑005)
* `07_summit_match.py` computes the proportion of top‑10 CRE summit positions that align within ±5 bp between MACS2 narrowPeak files and the generated bigWig tracks. The metric `summit_match_pct_top10` is reported in the statistical summary.

### 8. Null‑Synthetic Mode (Addressing scientific_soundness-242e2d1f)
* The `--null-synthetic` flag generates synthetic ChIP‑seq and eQTL data **without any true correlation** between ΔPeakSignal and log₂FC. Running the full pipeline on this data must yield non‑significant β₁ (adjusted p > 0.05), demonstrating that the analysis does not produce false positives when no signal exists.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|---|---|---|
| **Synthetic mode for CI** | No verified real datasets; enables pipeline testing. | Using unrelated public datasets would violate the spec's data‑fit requirement. |
| **FDR 0.01 for MACS2** | Spec‑mandated; standard for yeast ChIP‑seq. | Relaxed thresholds would reduce stringency. |
| **LMM over GLM** | Accounts for gene‑level random effects. | Simple GLM ignores hierarchical structure. |
| **SIMEX correction** | Addresses measurement error attenuation. | Ignoring error would bias β₁ toward zero. |
| **Motif weighting** | Improves power for distal CREs with weak evidence. | Unweighted model would dilute true signals. |
| **ATAC-Deferred Mode** | Allows pipeline to run when ATAC is missing, with appropriate caveats. | Aborting would prevent any analysis when ChIP/eQTL are available. |
| **Permutation count** | 10 k provides a stable empirical p‑value; CI mode caps at 1 k for runtime. | Fewer permutations risk unstable null distribution. |
| **Null‑synthetic mode** | Provides a controlled test of false‑positive control. | No null test would leave the pipeline unvalidated for type I error. |

## Limitations & Future Work

* **Causal inference**: Without perturbation experiments (e.g., CRISPRi) or instrumental variables, results remain associational. The term "drive" is interpreted as "predicts" in the output.
* **Power analysis**: Formal sample‑size calculation is performed in Phase 2; if power is low, this is reported in the PDF.
* **Data availability**: Real ChIP‑seq, eQTL, and ATAC‑seq datasets must be sourced by the user. The pipeline will abort if ChIP/eQTL are missing but will run in "ATAC-Deferred Mode" if only ATAC is missing.
* **Measurement error**: SIMEX relies on a Poisson-based estimate if replicates are missing; more precise replicates would improve correction.
* **Future extensions**: Incorporate Mendelian Randomization using eQTL as instruments once suitable datasets are available.