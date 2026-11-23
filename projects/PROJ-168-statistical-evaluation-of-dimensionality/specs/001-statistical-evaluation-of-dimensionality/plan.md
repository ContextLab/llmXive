# Implementation Plan: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

**Branch**: `001-gene-regulation` | **Date**: 2026-10-23 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (1) **verify the availability of three open scRNA‑seq datasets** (using documented open substitutes for the original GEO accessions, see Phase 0), (2) download, checksum, and preprocess each (log‑CPM, HVG selection, deterministic subsampling), (3) compute global intrinsic dimensionality (Levina‑Bickel) and local density (average 15‑NN distance) on the high‑dimensional matrix, (4) generate PCA, t‑SNE, and UMAP embeddings with fixed hyper‑parameters, (5) run Leiden clustering (resolution = 0.5) on each embedding and compute ARI/NMI fidelity metrics **with a shift‑and‑logit transformation for ARI**, (6) perform a sensitivity sweep over silhouette‑score thresholds {0.4, 0.5, 0.6) and **report variance with a 95 % bootstrap confidence interval** (no binary pass/fail), (7) fit a **mixed‑effects model** to test the effect of method type on fidelity **while explicitly acknowledging limited power** and **additionally run a permutation‑based ANOVA** to provide a robust inference under the small sample size, (8) produce validated JSON/YAML reports and figures. All steps respect FR‑001 … FR‑008 and SC‑001 … SC‑006, with explicit power‑limitation acknowledgement and full constitutional compliance.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `scanpy==1.10.2`, `scikit-learn==1.5.0`, `umap-learn==0.5.6`, `leidenalg==0.10.2`, `pandas==2.2.2`, `numpy==2.0.0`, `psutil==6.0.0`, `statsmodels==0.14.2`, `pingouin==0.5.4`, `pyyaml==6.0.1`, `datasets==2.20.0`  
- **Storage**: File system under `data/` (raw, processed, results).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤14 GB disk, ≤6 h). All methods run on CPU; no GPU required.  
- **Constraints**: Peak RSS ≤ 7 GB (SC‑003); total wall‑clock ≤ 21 600 s (SC‑004).  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | All random generators seeded (42 for sampling, 12345 for optional subsampling, 42 for Leiden). URLs are immutable. |
| II. Verified Accuracy | PASS | Every external dataset URL is taken from the “Verified datasets” block or, when unavailable, an open substitute is explicitly documented (see Phase 0). |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded in `data/manifest.json`; raw files never overwritten. |
| IV. Single Source of Truth | PASS | Each metric originates from a single row in `data/` and a single script in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/projects/...yaml`. |
| VI. Geometric Characterization Protocol | PASS | Intrinsic dimensionality and local density computed **before** any embedding. |
| VII. Ground‑Truth Fidelity Validation | PASS | Fidelity (ARI/NMI) always compared to independent cell‑type labels. |

## Phase Overview & FR/SC Mapping
| Phase | Core Tasks | FR(s) | SC(s) |
|-------|------------|-------|-------|
| **0 – Data Availability Verification** | Load manifest, confirm each dataset contains a `counts` matrix; abort if missing. Document open substitutes for the three GEO accessions (see Research §1). | FR‑001 (dataset existence) | SC‑003, SC‑004 |
| **1 – Ingestion & Preprocessing** | Download (via `datasets.load_dataset`), checksum, deterministic subsample (≤ 5 000 cells, seed = 12345), log‑CPM, variance‑stabilizing HVG selection, store Parquet. | FR‑001, FR‑002, FR‑003 | SC‑003, SC‑004 |
| **2 – Geometric Diagnostics** | Levina‑Bickel intrinsic dimensionality (k = 15, 10 000 random unordered cell pairs, seed = 42) and average 15‑NN distance (local density) on the high‑dim matrix. | FR‑002, FR‑003 | SC‑003 |
| **3 – Embedding Generation** | PCA (30 PCs, 2‑D projection), t‑SNE (perplexity 30, 1 000 iters), UMAP (n_neighbors 15, min_dist 0.1). Save 2‑D coordinates (CSV) and full PCA matrix (Parquet). | FR‑004 | SC‑003, SC‑004 |
| **4 – Primary Fidelity Calculation** | Leiden clustering on each embedding (resolution = 0.5, seed = 42). Compute **Adjusted Rand Index (ARI)** and **Normalized Mutual Information (NMI)** against ground‑truth labels. **Transformation:**<br>• **ARI** is first shifted to `(ARI + 1) / 2` to map to `[0,1]`, then **logit‑transformed**.<br>• **NMI** (already in `[0,1]`) is **logit‑transformed** directly. Store in `data/metrics/fidelity_*.json`. | FR‑005 | SC‑006 (no missing values) |
| **5 – Sensitivity Sweep** | For silhouette thresholds {0.4, 0.5, 0.6}: re‑run Leiden, recompute ARI/NMI, calculate **variance across thresholds** and **95 % bootstrap confidence interval** (10 000 resamples). **Only reporting** – no binary pass/fail (aligns with SC‑001). | FR‑007 | SC‑001 |
| **6 – Statistical Analysis** | **Mixed‑effects model** (required by FR‑006): `logit_fidelity ~ method + intrinsic_dimensionality + local_density + cell_count + gene_count + batch + (1|dataset)`. Because only three datasets are available, the model is **acknowledged as under‑powered** and its results are interpreted cautiously. <br>**Supplementary permutation‑based ANOVA** (10 000 permutations) with the same fixed effects (method, intrinsic_dimensionality, local_density, cell_count, gene_count, batch) provides a robust p‑value for the `method` effect. <br>**Assumption Checks:** Shapiro‑Wilk on residuals (if p < 0.05 rely on permutation p‑value); VIF computed for all predictors (abort if any VIF ≥ 5). <br>**Multiple‑Testing:** Benjamini‑Hochberg applied to all p‑values (SC‑002). | FR‑006, FR‑008 | SC‑002, SC‑005 |
| **7 – Reporting & Contract Validation** | Assemble JSON/YAML summary, generate sensitivity plots, validate all outputs against schemas in `contracts/`. | All FRs (output artifacts) | All SCs (memory, runtime, completeness) |

## Edge‑Case Handling
- **< 500 cells** → skip intrinsic‑dimensionality & local‑density computation, log warning, continue with embeddings.  
- **Missing ground‑truth labels** → mark fidelity as “Unavailable” for that dataset; exclude from statistical analysis.  
- **Leiden non‑convergence** → retry once with same seed; if still failing, record “Unavailable” and proceed.  

## Compute Feasibility
- Sparse matrix representation keeps peak RSS at a modest, few‑gigabyte level.  
- t‑SNE & UMAP on ≤ 5 000 cells finish < 30 min each on the free runner.  
- Total wall‑clock expected < 3 h; abort if > 21 600 s (SC‑004).  

## Power & Limitations
- With only three datasets the mixed‑effects model is **under‑powered**; we therefore **supplement** it with a permutation ANOVA and **explicitly acknowledge** this limitation in the final report and discussion (SC‑002 discussion).  

## Spec‑Amendment Note
Because the original GEO accessions do **not** provide publicly downloadable raw count matrices, we have substituted open, verifiable datasets (see Phase 0). This deviation will be recorded as a formal spec amendment (see Constitution VI).  

## Task List (ordered)
1. `code/phase0_verify_raw_counts.py` – verify raw count presence, write `data/manifest.json`.  
2. `code/phase1_preprocess.py` – checksum, deterministic sampling, log‑CPM, HVG, write Parquet.  
3. `code/phase2_geometry.py` – Levina‑Bickel intrinsic dim, 15‑NN local density, store JSON.  
4. `code/phase3_embeddings.py` – PCA, t‑SNE, UMAP, save CSV/Parquet.  
5. `code/phase4_fidelity_fixed.py` – Leiden (resolution 0.5), ARI/NMI, shift‑and‑logit ARI, write `data/metrics/fidelity_*.json`.  
6. `code/phase5_sensitivity.py` – silhouette‑threshold sweep, variance + 95 % CI calculation, store summary.  
7. `code/phase6_mixed_effects.py` – fit mixed‑effects model (with power disclaimer) **plus** run permutation ANOVA; VIF check; BH correction; write `data/results/statistical_result.yaml`.  
8. `code/phase7_reporting.py` – aggregate tables, generate plots, validate contracts.  
9. `Snakefile` – orchestrates all phases, includes a `verify_data_availability` rule that aborts if any dataset is “Unavailable”.  

---



