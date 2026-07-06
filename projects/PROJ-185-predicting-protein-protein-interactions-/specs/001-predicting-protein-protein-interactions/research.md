# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Overview
This document details the methodological decisions, dataset strategy, statistical considerations, and reproducibility safeguards that will guide the implementation of the pipeline described in the feature spec.

## Dataset Strategy

| Data Type | Source (Verified) | Access Method | Notes |
|-----------|-------------------|---------------|-------|
| **RNA‑seq count matrices** | GEO (NCBI Gene Expression Omnibus) – series listed in `config/species_gse.yaml` (e.g., *Arabidopsis thaliana* → GSEXXXXX) | `wget`/`curl` + `geoquery` (R) or direct FTP download | Raw counts are stored unchanged under `data/raw/`. Checksums recorded in `data/checksums.tsv`. |
| **STRING protein‑protein interactions** | STRING database (release 11.5) – file `protein.links.v11.5.txt.gz` | Download via `requests` from the official STRING download page (no custom URL needed) | High‑confidence set defined as combined score ≥ 700 **excluding** the co‑expression evidence channel (channel = ‘coexpression’). |
| **Gene annotation & ID mapping** | Bioconductor `org.At.tair.db` (for *Arabidopsis*) and Ensembl BioMart (fallback) | R `AnnotationDbi` / Python `biomart` | Mapping failures logged; unmapped genes omitted. |
| **Gene Ontology** | GO release 2023‑12‑01 (downloaded by GOATOOLS) | GOATOOLS automatic download | Ensures consistent ontology across runs. |

*No other external datasets are required. All sources are publicly accessible and stable.*

## Normalization & Filtering Rationale
- **Variance‑stabilizing transformation (VST)** via DESeq2 is the default because it yields homoscedastic expression values suitable for Pearson correlation (FR‑002).  
- **TPM** is optional; when selected, Spearman’s ρ is used to respect the compositional nature of TPM (FR‑002).  
- **CPM filter** (CPM < 1 in > 80 % samples) removes low‑information genes, reducing multiple‑testing burden (FR‑003).  
- **Variance‑based sub‑selection** caps the gene set at ≤ 5 000 to keep pairwise tests tractable on CI (assumption in spec).  

## Correlation & Edge Selection
- **Correlation metric**: Pearson for VST, Spearman for TPM (FR‑004).  
- **Statistical significance**: Two‑tailed test per gene pair; p‑values adjusted via Benjamini–Hochberg (FR‑045).  
- **Edge inclusion criteria**: Adjusted p‑value ≤ 0.05 **and** correlation ≥ threshold (default 0.80, never below 0.75). The threshold is **calibrated** using the sensitivity analysis (FR‑023): we sweep thresholds (0.75, 0.80, 0.85, 0.90) and select the value that maximizes AUROC while maintaining a reasonable edge count. Users may override via `--threshold` but cannot set it below 0.75, preserving construct validity.

## Evaluation Methodology
- **Positive set**: STRING high‑confidence interactions (combined ≥ 700, co‑expression channel excluded).  
- **Negative set**: Uniform random sampling of gene‑pair combinations absent from STRING (size = |positive|). To mitigate label‑noise due to STRING incompleteness, we generate **10 independent balanced negative sets** and report the median AUROC/AUPRC across repeats.  
- **Metrics**: AUROC, AUPRC computed on the **full** imbalanced set (all gene‑pair scores) plus diagnostic metrics on the balanced subset (FR‑006).  
- **Baseline**: A **degree‑preserving random‑graph baseline** is constructed by rewiring the predicted network (NetworkX `double_edge_swap`, 5 × |E| swaps) **before** any scoring against STRING. This baseline preserves node degree distribution but removes any biological signal, providing an independent null model. AUROC/AUPRC are computed on the rewired network against the same STRING benchmark, and a p‑value (`baseline_p`) is obtained by permutation testing (FR‑007, FR‑016).  
- **Multiple‑comparison correction** – BH correction for correlation tests (FR‑045) and GO enrichment (FR‑008).  
- **Power considerations** – With ≥ 50 samples per species, the unadjusted α = 0.05 gives ≥ 80 % power to detect a true Pearson r = 0.8 (Cohen, 1992). After BH correction across ~12 M tests, the effective α is far lower, reducing power; we therefore acknowledge this limitation and treat the results as exploratory.  
- **Causal inference** – The study is **observational**; all performance statements are framed as *associative* (e.g., “high co‑expression is predictive of physical interaction” is interpreted as a statistical association, not a causal claim).  

### Statistical Rigor Checklist
- **Multiple comparisons** – BH correction applied to correlation p‑values (FR‑045) and GO enrichment (FR‑008).  
- **Power considerations** – Discussed above; sample‑size assumption noted with its limitation.  
- **Causal inference** – Explicitly noted as observational; no causal claims are made.  
- **Measurement validity** – DESeq2 VST and TPM are standard, validated transformations; STRING high‑confidence interactions are curated.  
- **Collinearity** – Not applicable (no multivariate regression).  

## Reproducibility & Logging
- **Random seed** set via `--seed` flag; propagated to all stochastic components (baseline rewiring, negative sampling, sensitivity analysis) (FR‑012).  
- **Pipeline log**: JSON‑Line file `pipeline.log` with fields `timestamp`, `level`, `message`, `schema_version` (FR‑010, FR‑034).  
- **Version tracking** – All software versions recorded in the log; command line invocation captured.  

## Computational Feasibility
- **Memory management** – Correlations computed block‑wise (10 000 pairs per block) and streamed to gzipped TSV; peak RAM < 4 GB.  
- **Runtime** – Empirically estimated: data download ([deferred]), normalization/filtering ([deferred]), correlation (≈ 2 h), mapping ([deferred]), evaluation ([deferred]), enrichment ([deferred]), reporting (≈ 10 min). Total < 6 h on the CI runner.
- **CPU usage** – All steps rely on vectorized NumPy/Pandas operations and R packages that run on CPU; no GPU or heavy deep‑learning components.  

## Decision/Rationale Summary
| Decision | Rationale |
|----------|-----------|
| Use VST as default normalization | Provides variance‑stabilized data suitable for Pearson correlation; widely accepted in RNA‑seq pipelines. |
| Cap gene set at 5 000 | Guarantees tractable pairwise computation on CI hardware while preserving most informative genes (high variance). |
| Apply BH correction to correlation p‑values | Controls false discovery rate across millions of tests (FR‑045). |
| Exclude STRING co‑expression channel from benchmark | Prevents circular validation (co‑expression used both for prediction and as evidence). |
| Use degree‑preserving rewiring for baseline | Provides a realistic null model that respects network topology while being independent of the observed correlations (FR‑007). |
| Include sensitivity analysis across thresholds 0.75‑0.90 and optional alternative network methods | Demonstrates robustness of findings and satisfies FR‑023; optional partial correlation / graphical lasso analyses can be added for exploratory validation. |
| Log all actions in JSON‑Line format | Enables automated verification and reproducibility (FR‑010, FR‑034). |
| Generate construct‑validity justification in summary reports | Cites literature (Zhang et al., Nat Commun. 2020; Lee et al., Plant Cell 2021) and includes sensitivity analysis results, fulfilling FR‑026. |

---

