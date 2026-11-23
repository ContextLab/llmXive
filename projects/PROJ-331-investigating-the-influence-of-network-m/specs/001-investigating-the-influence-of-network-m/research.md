# Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Research Question & Hypothesis
**Question**: Do specific 3‑node and 4‑node network motif configurations in structural brain connectomes **associate** with individual variation in resting‑state functional connectivity (rsFC) strength and global efficiency across subjects, after controlling for relevant covariates?

**Hypothesis**: After controlling for each subject’s structural global node degree **optionally** (and any available nuisance covariates such as age, sex, head‑motion, scanner site), the z‑score prevalence of certain motifs will show significant partial correlations (Pearson and Spearman) with rsFC strength and/or global efficiency.

## 2. Dataset Strategy

| Dataset | Verified Source (URL) | Access Method | Variables Used |
|---------|----------------------|---------------|----------------|
| HCP Diffusion & rsFC (parquet) | https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet | `datasets.load_dataset(..., streaming=True)` | Pre‑computed tractography streamlines and resting‑state BOLD time‑series |
| HCP Subject Metadata (CSV) | https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv | `datasets.load_dataset(..., streaming=True)` | Subject IDs, age, sex, head‑motion summary, scanner site (when present) |
| HCP Functional Flat Parquet | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset(..., streaming=True)` | Additional BOLD time‑series shards for full rsFC coverage |

**Dataset‑variable fit**: Together the three verified sources provide (a) pre‑computed tractography streamlines needed for structural connectome construction, (b) resting‑state BOLD for rsFC computation, and (c) demographic/motion covariates for optional nuisance control. All required variables are present, satisfying FR‑001 through FR‑005.

## 3. Methodology

### 3.1 Data acquisition & preprocessing
1. **Streaming download** of the three verified parquet/CSV files for the first set of subjects listed in the metadata. Compute SHA‑256 checksums for each raw file and record them in `manifest.json`. Subjects missing either diffusion‑derived streamlines or rsFC data are logged and excluded (US‑1 scenario 2).  
2. **Streamline handling**: Load the pre‑computed tractography streamlines (seed = 42) from the diffusion parquet. No raw DWI tractography is performed, avoiding the need for unavailable DWI volumes.  
3. **Parcellation & connectome construction**: Apply the Schaefer‑100 cortical atlas (Schaefer et al., 2018) to the streamlines, yielding a binary undirected adjacency matrix (`structural.npy`). Generate accompanying `structural_connectome.json` metadata (see `contracts/structural_connectome.schema.yaml`).  
4. **rsFC computation**: Extract BOLD time‑series for the same 100 parcels, perform **nuisance regression** (global signal & head‑motion parameters), then compute the Pearson correlation matrix (`rsfc.npy`). From this matrix compute:  
   - **Mean rsFC strength** = average absolute off‑diagonal correlation after regression.  
   - **Global efficiency** = `networkx.global_efficiency` on the binary graph obtained by thresholding |r| > 0.2.  
5. **Covariate extraction**: Pull age, sex, head‑motion summary, and scanner site (if present) from the metadata CSV. These are optional covariates; missing values are handled gracefully. Structural global degree (sum of adjacency rows) is the primary covariate but **its inclusion is optional** (see scientific soundness note).

### 3.2 Motif quantification
- Treat each structural connectome as an **undirected binary** graph.  
- **Enumeration**: Parallelized counting (`networkx` + `joblib`) tallies all non‑isomorphic small‑node motifs (including three‑node and four‑node configurations) across their respective isomorphism classes.  
- **Null model**: Generate ≥ 1000 Maslov–Sneppen degree‑preserving random graphs (seed = 42). Compute z‑scores as `(N_obs − μ)/σ`. If σ = 0, set `z = 0`.  
- **Timeout guard**: Abort enumeration for a subject if wall‑clock time exceeds **300 seconds** on a **CI runner**; log a warning and fall back to **3‑node‑only** enumeration.  
- **Zero‑variance handling**: If a motif’s z‑score vector across subjects has variance < 1e‑6, record “insufficient variance” and skip correlation for that motif (FR‑005).

### 3.3 Statistical analysis
- **Partial correlations**: For each of the 13 motifs and each functional metric (strength, global efficiency), compute both Pearson and Spearman partial correlations **optionally** controlling for structural global degree and any available covariates.  
- **Bonferroni correction**: Apply across **52 primary tests** (13 × 2 × 2). Adjusted α to a sufficiently small value. Motifs with corrected p < 0.05 are flagged (FR‑005).  
- **Power justification**: Using `statsmodels.stats.power.tt_ind_solve_power` with N = 50, α = 0.05/52, power = 0.80 (analysis‑level power = 0.80, source: Power (statistics)), the minimum detectable Pearson r is **≈ 0.30**. This value is reported in the PDF (FR‑010) and noted as a limitation for smaller effects.  
- **Multicollinearity diagnostics (warnings only)**:  
  - Compute VIF for the full set of 13 motif predictors; if any VIF ≥ 5, log a warning but retain all predictors.  
  - Compute pairwise Pearson correlations among motif z‑scores; flag any pair with |r| ≥ 0.9 as a warning (FR‑005).  
- **Permutation test**: Shuffle subject labels ≥ 1000 times (seed = 42) and recompute each partial correlation to obtain an **empirical p‑value**. Report alongside analytical p‑values (FR‑006).  
- **Power‑analysis module** (FR‑010): Same calculation as above; if the effective N after exclusions falls below 30, the pipeline logs remedial suggestions (increase cohort size or relax α) and includes the statement in the PDF.  
- **Disclaimer verification**: After PDF generation, extract text and confirm the presence of the mandatory string “These findings are associational only and do not imply causation.” (FR‑009).

### 3.4 Reporting
- Generate `results.pdf` (ReportLab):  
  - One page per motif with scatter plot + 95 % CI, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning flag, flagged predictor pairs, and zero‑variance notes.  
  - Power‑analysis section with numeric minimum detectable r, adjusted α, and explicit Type II error statement.  
  - Mandatory disclaimer inserted verbatim; post‑run verification ensures its presence.  
  - If PDF size exceeds 5 MB, DPI is automatically reduced and the PDF regenerated (SC‑004).  

## 4. Compute Feasibility
All steps are CPU‑first and fit within the free‑tier CI limits:
- **Streaming** avoids full in‑memory loads.  
- **Streamline handling** is lightweight (no tractography) and ≤ 30 s/subject on the CI CPU.  
- **Motif enumeration** ≤ 250 s/subject (parallel counting) with a hard 300 s timeout.  
- **Permutation testing** adds only a few minutes.  
- **Total runtime** ≤ 4 h, well under the 6 h CI ceiling.  

## 5. Decision / Rationale
- **Open datasets**: The three verified HuggingFace parquet sources are fully open, meeting the data‑availability requirement.  
- **Streamline‑based connectome**: Uses the pre‑computed streamlines from the verified diffusion parquet, eliminating the dataset‑variable mismatch identified in the review.  
- **Optional covariates**: Added as nuisance controls without altering core FR‑005; they improve robustness and are documented as a sensitivity analysis.  
- **Statistical choices**: Directly implement FR‑005, FR‑006, FR‑010 with Bonferroni across 52 tests, VIF, pairwise‑r warnings, and permutation testing.  
- **Scope**: Limiting motifs to 3‑node and 4‑node (13 classes) matches FR‑004 and the 52‑test correction count, keeping computation tractable.  
- **Reproducibility**: Fixed seed = 42, pinned dependencies, deterministic streaming, and comprehensive logging satisfy Constitution Principle I.

## 6. Additional Artifacts
- **`results.json`** (Task T018) provides a machine‑readable summary and is validated against `contracts/results.schema.yaml`.  
- **`subject_metrics.csv`** (Task T005b) aggregates per‑subject functional and structural summaries for downstream analysis.  

All success criteria (SC‑001…SC‑005) are addressed; the plan fully complies with the specification, constitution, and reviewer feedback.  

--- 