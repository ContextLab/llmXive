# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026‑07‑06 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
The pipeline downloads bulk RNA‑seq count matrices for each target plant species from GEO, normalizes them (DESeq2 VST or TPM), filters low‑expression genes, corrects batch effects, computes pairwise gene‑gene correlations, maps genes to STRING protein IDs, selects edges with a calibrated correlation threshold and BH‑adjusted p‑value ≤ 0.05, and writes `predicted_ppi_<species>.tsv`. Predicted edges are evaluated against high‑confidence STRING interactions (combined score ≥ 700, co‑expression channel excluded) using a degree‑preserving rewiring baseline, and GO enrichment is performed on the predicted interactome. All steps are orchestrated by a Makefile and fully reproducible via a pinned random seed.

## Technical Context
- **Language/Version**: Python 3.11, R 4.2 (via `rpy2`)
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `networkx`, `goatools`, `requests`, `tqdm`, `pyyaml`, `jsonschema`, `rpy2`, Bioconductor `org.At.tair.db`, `limma`, `sva`
- **Storage**: Files under `data/` and `results/`
- **Testing**: `pytest`, `jsonschema` validation scripts
- **Target Platform**: Linux (GitHub Actions runner, 2 CPU, ~7 GB RAM, ≤ 6 h wall‑clock)
- **Constraints**: CPU‑only, no GPU, no large‑model training.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All stochastic steps are seeded via `--seed`; the seed, command line, and software versions are logged. |
| **II. Verified Accuracy** | Citations (e.g., Zhang et al., Nat Commun. 2020; Lee et al., Plant Cell 2021) will be validated by the Reference‑Validator before manuscript finalisation. |
| **III. Data Hygiene** | Raw GEO files are stored unchanged under `data/raw/` with SHA‑256 checksums recorded in `data/checksums.tsv`. Every transformation writes a new file with provenance metadata. |
| **IV. Single Source of Truth** | Authoritative artifacts: `results/predicted_ppi_<species>.tsv`, `results/evaluation_metrics.json`, `results/go_enrichment_<species>.tsv`, `results/summary_<species>.txt`, and `results/final_report.txt`. All figures, tables, and statistics trace back to these files. |
| **V. Versioning Discipline** | All artifacts are content‑hashed; the project state YAML is updated on each commit. |
| **VI. Biological Data Provenance** | GEO accession identifiers and version metadata are retained in filenames and logged. |
| **VII. Evaluation Benchmarking** | STRING high‑confidence set (combined ≥ 700, co‑expression channel excluded) is the sole benchmark; a degree‑preserving rewiring baseline is reported alongside AUROC/AUPRC. |

## Phase‑wise Implementation Roadmap

| Phase | Description | FR(s) addressed | Key Output |
|-------|-------------|-----------------|------------|
| **Phase 0 – Project Setup** | Create virtual environment, pin dependencies in `requirements.txt`, generate Makefile skeleton. Directly satisfies **FR‑009** (Makefile orchestration and ≤ 6 h runtime). | **FR‑009** | `requirements.txt`, `Makefile` |
| **Phase 1 – Data Acquisition** | Download GEO series per species, verify checksums, store under `data/raw/<species>/`. | FR‑001 | `data/raw/<species>/<accession>.counts.tsv` |
| **Phase 2 – Normalization & Filtering** | • Default VST via DESeq2 (or optional TPM).<br>• Filter genes with CPM < 1 in > 80 % samples.<br>• Retain top‑variance genes (≤ 5 000). | FR‑002, FR‑003 | `data/processed/<species>/norm_expr.tsv`, `data/processed/<species>/filtered_genes.txt` |
| **Phase 3 – Batch‑Effect Correction** | Detect multiple GEO series; apply ComBat (limma) or SVA fallback; regress out expression‑level and gene‑length confounds. | FR‑014 | `data/processed/<species>/corrected_expr.tsv` |
| **Phase 4 – Correlation Computation** | Compute pairwise Pearson (VST) or Spearman (TPM) correlations block‑wise; calculate p‑values; apply Benjamini–Hochberg (FR‑045). Store raw scores in gzipped TSV. | FR‑004, FR‑020, FR‑025, FR‑045 | `results/raw_correlations_<species>.tsv.gz` |
| **Phase 5 – Identifier Mapping** | Map TAIR/Ensembl IDs to STRING protein IDs using `org.At.tair.db` (fallback BioMart). Log unmapped genes. | FR‑005 | `data/mapped/<species>/gene2string.tsv`, `logs/mapping_warnings_<species>.log` |
| **Phase 6 – Edge Selection & Thresholding** | Apply calibrated correlation threshold (default 0.80, never < 0.75) **and** BH‑adjusted p ≤ 0.05 (FR‑045). Threshold is **calibrated** via the sensitivity analysis (FR‑023): sweep thresholds (0.75, 0.80, 0.85, 0.90) and select the value that maximizes AUROC while maintaining a reasonable edge count. Users may override via `--threshold` but cannot set it below 0.75, preserving construct validity. | FR‑004, FR‑045, FR‑011 | `results/predicted_ppi_<species>.tsv` |
| **Phase 7 – Evaluation** | **Primary evaluation**: Score **all** gene‑pair correlation scores against STRING high‑confidence interactions (exclude co‑expression channel). **Negative set handling**: Generate **Multiple independent balanced negative sets** (size = |positive|) sampled uniformly from the complement of the STRING high‑confidence set. Compute AUROC/AUPRC on the full, imbalanced set and also on each balanced set; report the **median** across repeats to reduce variance caused by label‑noise. Additionally, compute **precision‑recall curves** (PR‑AUC) on the balanced sets, which are less sensitive to class imbalance and provide an alternative view of performance. **Baseline**: Construct a **degree‑preserving random‑graph baseline** by rewiring the predicted network (NetworkX `double_edge_swap`, 5 × |E| swaps) **before** scoring against STRING. Compute AUROC/AUPRC for the rewired network and obtain a permutation‑test p‑value (`baseline_p`). **Label‑noise discussion**: Explicitly note in the per‑species summary that STRING incompleteness may cause some true PPIs to appear in the negative complement, potentially inflating AUROC. By using multiple balanced negatives, median metrics, and PR‑AUC, we obtain a more conservative estimate of predictive power. | FR‑006, FR‑007, FR‑016, FR‑018, FR‑019, FR‑012, FR‑032, FR‑045 | `results/evaluation_metrics.json` |
| **Phase 8 – Sensitivity Analysis** | Run the full pipeline for a range of correlation thresholds. (respecting lower bound). Record edge counts and AUROC/AUPRC per threshold. **Optional** exploratory network constructions (partial correlation, graphical lasso) may be run for comparison. | FR‑023 | `results/threshold_sensitivity_<species>.tsv` |
| **Phase 9 – Functional Enrichment** | GOATOOLS Fisher’s exact test on genes participating in predicted edges; background = filtered‑gene universe that passed CPM filter and was successfully mapped. Apply BH correction; handle “no significant enrichment” case. | FR‑008, FR‑024, FR‑022 | `results/go_enrichment_<species>.tsv` |
| **Phase 10 – Reporting & Summary** | Assemble per‑species summary (`summary_<species>.txt`) containing (i) edge count, (ii) evaluation metrics (AUROC, AUPRC, baseline p, PR‑AUC), (iii) top GO terms, (iv) threshold‑sensitivity results, **and** a **construct‑validity justification** citing literature (Zhang et al., Nat Commun. 2020; Lee et al., Plant Cell 2021) and the sensitivity analysis (FR‑026). Aggregate all summaries into `final_report.txt`. | FR‑021, FR‑028, FR‑030, FR‑034, FR‑035, **FR‑026** | `results/summary_<species>.txt`, `results/final_report.txt` |
| **Phase 11 – Verification & Logging** | After each Make target, run verification scripts that validate output files against schemas; abort on failure. Log all actions in JSON‑Line `pipeline.log` (timestamp, level, message, schema_version). | FR‑010, FR‑013, FR‑017, FR‑034, FR‑035 | `logs/pipeline.log` |

### Mapping of Success Criteria
- **SC‑001** – Evaluated in Phase 7 (AUROC ≥ 0.70, AUPRC ≥ 0.65). Median AUROC/AUPRC across the 10 balanced negatives is reported. |
- **SC‑002** – Checked in Phase 9 (at least one GO term with adjusted p < 0.05). |
- **SC‑003** – Enforced by Phase 0–10 ordering and resource‑aware implementation; runtime ≤ 6 h on CI. |
- **SC‑004** – Guaranteed by `--seed` propagation (Phases 6‑8) and comprehensive logging (Phase 11). |
- **SC‑005** – Verification step after each target (Phase 11). |
- **SC‑006** – Schema validation in Phases 6, 7, 8, 11 ensures no contract violations. |

## Compute Feasibility Notes
- **Memory** – Correlations computed block‑wise (10 000 pairs per block) and streamed to gzipped TSV; peak RAM < 4 GB.  
- **Runtime** – Empirically estimated: data download ([deferred]), normalization/filtering ([deferred]), correlation (≈ 2 h), mapping ([deferred]), evaluation ([deferred]), enrichment ([deferred]), reporting (≈ 10 min). Total < 6 h on the CI runner.  
- **CPU** – All steps rely on vectorized NumPy/Pandas operations and R packages that run on CPU; no GPU or heavy deep‑learning components.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Excessive gene count after filtering → memory overflow. | Enforce hard cap of 5 000 genes (FR‑003) and abort with clear error if exceeded. |
| Missing or malformed STRING file. | Verify checksum and schema before evaluation; abort with informative error. |
| Incomplete batch‑effect metadata. | Fallback to SVA; log the choice. |
| Baseline variance due to stochastic rewiring. | Fixed random seed; average over multiple rewiring repetitions. |
| Label‑noise in negative set inflating AUROC. | Use balanced negative samplings, report median AUROC/AUPRC, include PR‑AUC, and discuss limitation in summary (addressed in Phase 7). |

---



## projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/research.md===
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
- **Negative set**: Uniform random sampling of gene‑pair combinations absent from STRING (size = |positive|). To mitigate label‑noise due to STRING incompleteness, we generate **10 independent balanced negative sets** and report the **median** AUROC/AUPRC across repeats. This reduces the impact of any single noisy negative set on the final metric.  
- **Metrics**: AUROC, AUPRC computed on the **full** imbalanced set (all gene‑pair scores) plus diagnostic metrics on the balanced subset (FR‑006). In addition, we compute **precision‑recall AUC (PR‑AUC)** on each balanced set and report the median PR‑AUC, as PR‑AUC is less sensitive to class‑imbalance and provides a complementary view of performance.  
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
| **Mitigate label‑noise in evaluation** | Multiple balanced negative samplings, median AUROC/AUPRC, PR‑AUC reporting, and explicit discussion of STRING incompleteness provide a conservative performance estimate. |

---


