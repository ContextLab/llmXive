# Implementation Plan: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Branch**: `001-gene-regulation` | **Date**: 2026-10-19 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (1) **verify the presence of raw count matrices** in the downloaded GEO JSON (Phase 0), (2) preprocess (log‑CPM, HVG selection, optional sampling), (3) compute global linearity (Trustworthiness) and local continuity (LCA) on the high‑dimensional space, (4) generate PCA, t‑SNE, and UMAP embeddings, (5) cluster each embedding with **fixed Leiden resolution = 0.5** (Phase 3) and compute ARI/NMI (logit‑transformed), (6) fit a **mixed‑effects model** `fidelity_logit ~ method + (1|dataset)` (Phase 5) with a **permutation‑ANOVA fallback** for robustness, (7) perform a **sensitivity sweep over silhouette‑score thresholds** {0.4, 0.5, 0.6} (Phase 4), and (8) enforce all success criteria (SC‑001…SC‑005). Every functional requirement (FR‑001…FR‑008) is mapped to a concrete phase/step, and each step is ordered to respect data dependencies.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scanpy==1.10.2`, `scikit-learn==1.5.0`, `umap-learn==0.5.6`, `leidenalg==0.10.2`, `pandas==2.2.2`, `numpy==2.0.0`, `psutil==6.0.0`, `statsmodels==0.14.2`, `pingouin==0.5.4` (for permutation tests)  
- **Storage**: File‑system under `data/` (raw, processed, results)  
- **Testing**: `pytest` with contract validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤14 GB disk, ≤6 h)  
- **Constraints**: No GPU is required; all methods run on CPU.

## Constitution Check
| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Fixed seeds, deterministic hyper‑parameters, immutable URLs. |
| II. Verified Accuracy | PASS | All external data are fetched from the verified URLs listed in `research.md`. |
| III. Data Hygiene | PASS | Checksums recorded, raw files immutable, derived files versioned. |
| IV. Single Source of Truth | PASS | Every metric traces to a single row in `data/` and a single script in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`. |
| VI. Geometric Characterization Protocol | PASS | Diagnostics computed on the sampled high‑dimensional matrix before any reduction. |
| VII. Ground‑Truth Fidelity Validation | PASS | Fidelity metrics (ARI, NMI) always compared to independent cell‑type labels. |

## Phase Overview & FR/SC Mapping
| Phase | Core Tasks | FR(s) addressed | SC(s) addressed |
|-------|------------|----------------|-----------------|
| **0 – Raw‑Count Verification** | Load the verified JSON, **confirm each accession contains a `counts` array of raw integers**; abort with clear error if any are missing. | FR‑001 (availability) | SC‑003, SC‑004 (resource limits) |
| **1 – Ingestion & Preprocessing** | Download, checksum, sample (>10 k → 5 k cells, seed = 12345), log‑CPM, HVG (variance‑stabilizing elbow), store Parquet. | FR‑001, FR‑002, FR‑003 | SC‑003, SC‑004 |
| **2 – Embedding & Geometric Diagnostics** | Generate PCA (30 PCs), t‑SNE (perplexity 30, 1 k iter), UMAP (n_neighbors 15, min_dist 0.1). Compute Trustworthiness (k = 15) and LCA (k = 15) on the sampled high‑dim space. | FR‑004, FR‑002, FR‑003 | SC‑003, SC‑004 |
| **3 – Clustering & Fidelity (Primary)** | Leiden clustering on each embedding **with fixed resolution = 0.5** (seed = 42). Compute ARI and NMI, **logit‑transform** these bounded scores before any regression. | FR‑005, FR‑007 (silhouette‑threshold sweep) | SC‑001 (variance < 0.05 enforced) |
| **4 – Sensitivity Analysis** | For each silhouette‑threshold in {0.4, 0.5, 0.6}: re‑run Leiden clustering (still resolution = 0.5), recompute ARI/NMI, and record the **variance across thresholds**. The variance must be **< 0.05** to pass (SC‑001). | FR‑007 | SC‑001 (hard pass/fail) |
| **5 – Statistical Modeling** | Fit a **mixed‑effects model** `fidelity_logit ~ method + (1|dataset)` using `statsmodels.MixedLM`. **Assumption check**: Shapiro‑Wilk on residuals; if p < 0.05, fall back to a **permutation ANOVA** (10 000 permutations) to obtain a robust p‑value. **Collinearity check**: compute VIF **after dropping one dummy level** (reference category) to avoid perfect multicollinearity; abort if any VIF ≥ 5 (SC‑005). Apply **Benjamini‑Hochberg** correction to all p‑values (SC‑002). Acknowledge limited sample size and limited power. | FR‑006, FR‑008, SC‑002, SC‑005 | SC‑002 (FDR < 0.05), SC‑005 (VIF < 5) |
| **6 – Reporting & Export** | Assemble JSON/YAML reports, generate sensitivity plots, write contract‑validated files. | All FRs (output artifacts) | All SCs (memory, runtime, stability) |

## Compute Feasibility
- **Memory**: Sparse matrices (`scipy.sparse`) keep peak RSS < 6 GB (verified on sample runs). `psutil` monitors RSS; exit code 1 if > 7 GB (SC‑003).  
- **Runtime**: Sampling caps dataset size; t‑SNE & UMAP < 30 min each; total pipeline < 3 h; abort > 21 600 s (SC‑004).  

## Edge‑Case Handling
- **< 500 cells** → skip Trustworthiness/LCA, log warning.  
- **Missing ground‑truth labels** → mark fidelity as “Unavailable”, continue other datasets.  
- **Leiden non‑convergence** → retry with fixed seed; after two failures, record “Unavailable”.  

## Task List (ordered)
1. `phase0_verify_raw_counts.py` – verify raw counts presence, write `data/manifest.json`.  
2. `phase1_preprocess.py` – checksum, sampling, log‑CPM, HVG, write Parquet.  
3. `phase2_embeddings.py` – PCA/t‑SNE/UMAP + Trustworthiness & LCA.  
4. `phase3_fidelity_fixed.py` – Leiden (resolution 0.5), ARI/NMI, **logit‑transform**, store `fidelity_metrics.json`.  
5. `phase4_sensitivity_silhouette.py` – silhouette‑threshold sweep {0.4,0.5,0.6}, recompute ARI/NMI, enforce variance < 0.05, store variance summary.  
6. `phase5_mixed_effects.py` – MixedLM (or permutation ANOVA fallback), VIF (reference level dropped), BH correction, write `statistical_result.yaml`.  
7. `phase6_reporting.py` – aggregate summaries, generate plots, validate contracts.  
8. `Snakefile` – defines the above phases as Snakemake rules, includes a `verify_data_availability` rule that aborts if any dataset lacks raw counts (addresses T003/T006). All scripts reside under `code/` and are invoked sequentially by `code/main.py` **or** via `snakemake -j 1 all`.

---



