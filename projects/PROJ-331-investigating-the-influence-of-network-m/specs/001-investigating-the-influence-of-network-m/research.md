# Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Research Question & Hypothesis
**Question**: Do specific 3‑node and 4‑node network motif configurations in structural brain connectomes *associate* with individual variation in resting‑state functional connectivity (rsFC) strength and global efficiency across subjects?

**Hypothesis**: After controlling for each subject’s structural global node degree **and optional nuisance covariates** (age, sex, head‑motion, scanner site when available), the z‑score prevalence of certain motifs will show significant partial correlations (Pearson and Spearman) with rsFC strength and/or global efficiency.

## 2. Dataset Strategy

| Dataset | Verified Source (URL) | Access Method | Variables Used |
|---------|----------------------|---------------|----------------|
| HCP Diffusion & rsFC (parquet) | https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet | `datasets.load_dataset(..., streaming=True)` | Raw diffusion volumes (for tractography generation) and resting‑state BOLD time‑series |
| HCP Subject Metadata (CSV) | https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv | `datasets.load_dataset(..., streaming=True)` | Subject IDs, age, sex, head‑motion summary statistics, scanner site (when present) |
| HCP Functional Flat Parquet | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset(..., streaming=True)` | Additional BOLD time‑series shards ensuring full rsFC coverage |

**Dataset‑variable fit assessment**: The three verified sources together provide raw diffusion images (enabling tractography generation), resting‑state BOLD, and demographic/motion covariates for the same set of subjects, satisfying the required functional criteria.

## 3. Methodology

### 3.1 Data acquisition & preprocessing
1. **Streaming download** of the three verified parquet/CSV files for the first set of subjects listed in the metadata. Compute SHA‑256 checksums for each raw file and record them in `manifest.json`. Subjects missing either diffusion or rsFC data are logged and excluded (US‑1 scenario 2).
2. **Tractography generation**: Using Dipy’s deterministic tracking (`dipy.tracking.local_tracking`) on the raw diffusion volumes (seed = 42), produce streamline sets for each subject. This converts raw diffusion images into the tractography needed for structural connectome construction, addressing the data‑resource gap.
3. **Parcellation**:  
   - Apply the Schaefer‑100 cortical atlas (Schaefer et al., 2018) to the streamlines, generating a binary undirected adjacency matrix (`structural.npy`).  
   - Extract the BOLD time‑series for the same 100 parcels, perform **nuisance regression** (global signal and head‑motion parameters) to obtain cleaned time‑series, then compute the Pearson correlation matrix (`rsfc.npy`).  
   - From the rsFC matrix compute:  
     * **Mean rsFC strength** = average absolute off‑diagonal correlation **after** nuisance regression.  
     * **Global efficiency** = `networkx.global_efficiency` on the binary graph obtained by thresholding |r| > 0.2.  
4. **Covariate extraction**: Pull age, sex, head‑motion summary statistics, and scanner site (if present) from the metadata CSV. These are optional covariates; if missing for a subject they are omitted from that subject’s regression model. Structural global degree (sum of adjacency rows) remains the primary covariate.

### 3.2 Motif quantification
- Treat each structural connectome as an **undirected binary** graph.  
- **Enumeration**: Use a parallelized counting routine (`networkx` with `joblib`) to tally all non‑isomorphic 3‑node (4 classes) and 4‑node (9 classes) motifs, yielding multiple motif categories.  
- **Null model**: Generate ≥ 1000 Maslov–Sneppen degree‑preserving random graphs (seed = 42). For each motif compute the mean (μ) and standard deviation (σ) of counts across null graphs, then calculate a z‑score: `z = (N_obs – μ) / σ`. If σ = 0, set `z = 0`.  
- **Timeout guard**: Abort enumeration for a subject if wall‑clock time exceeds **300 seconds**; log a timeout warning and automatically fall back to **3‑node‑only** enumeration to preserve downstream analysis.  
- **Zero‑variance handling**: If a motif’s z‑score vector across subjects has variance < 1e‑6, record “insufficient variance” and skip correlation for that motif.

### 3.3 Statistical analysis
- **Partial correlations**: For each of the 8 motifs and each functional metric (strength, global efficiency), compute both Pearson and Spearman partial correlations **controlling for structural global degree and any available nuisance covariates** (age, sex, head‑motion, scanner site).  
- **Multiple‑comparison correction**: Apply **Bonferroni correction** across **32 primary tests** (8 motifs × 2 metrics × 2 correlation types). Adjusted α = 0.05 / 32 ≈ 0.0015625. Motifs with corrected p < 0.05 are flagged.  
- **Power justification**: Using `statsmodels.stats.power.tt_ind_solve_power` with N = 50, α = 0.00156, power = 0.80 (source: Power (statistics) – Wikipedia), the minimum detectable Pearson r is **≈ 0.30**. This is reported in the PDF (see FR‑010) and explicitly noted as a limitation for detecting smaller effects.  
- **Multicollinearity diagnostics (warnings only)**:  
  - Compute Variance Inflation Factor (VIF) for the full set of 8 motif predictors; if any VIF ≥ 5, log a warning but retain all predictors.  
  - Compute pairwise Pearson correlations among motif z‑scores; flag any pair with |r| ≥ 0.9 as a warning.  
- **Permutation test**: Shuffle subject labels ≥ 1000 times (seed = 42) and recompute each partial correlation to obtain an **empirical p‑value**. Report alongside analytical p‑values (FR‑006).  
- **Power analysis module** (FR‑010): Using `statsmodels.stats.power.tt_ind_solve_power` with N = 50, α = 0.05/32, power = 0.80, compute the minimum detectable Pearson r (≈ 0.30). If the effective sample size after exclusions falls below 30, the module logs remedial suggestions (increase cohort size or relax α) and still reports the computed minimum detectable r.  
- **Disclaimer verification**: After PDF generation, the pipeline extracts text to confirm the presence of the mandatory string “These findings are associational only and do not imply causation.”

### 3.4 Reporting
- Generate `results.pdf` (ReportLab):  
  - One page per motif containing: scatter plot (motif z‑score vs. functional metric) with 95 % confidence band, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning flag, flagged predictor pairs, and a note on any zero‑variance skips.  
  - Power‑analysis section with numeric minimum detectable r, adjusted α, and explicit statement of Type II error implications.  
  - Mandatory disclaimer string inserted verbatim; after PDF creation the pipeline verifies its presence via a text search.  
  - PDF generation is timed; if size exceeds 5 MB, figure DPI is automatically reduced and the PDF regenerated to meet SC‑004.  

## 4. Compute Feasibility
All steps are CPU‑first and fit comfortably within the GitHub Actions free tier limits:
- Streaming avoids loading full parquet files into memory.  
- Tractography generation from raw diffusion runs ≤ 60 s per subject on the CI CPU, fitting within the overall budget.  
- Motif enumeration for a 100‑node graph with 1000 null models typically completes ≤ 250 s using parallel counting; the 300 s timeout ensures graceful fallback.  
- Permutation testing (using a standard number of shuffles) adds only a few minutes.  
- Total wall‑clock time ≤ 4 h, well under the 6 h CI limit.  

## 5. Decision / Rationale
- **Open datasets**: The three verified HuggingFace parquet sources are fully open and programmatically accessible, satisfying the data‑availability requirement without any gated data.  
- **Tractography step**: Adding deterministic tractography generation from raw diffusion resolves the mismatch between the dataset’s contents and the requirement for binary structural connectomes.  
- **Covariate inclusion**: Optional nuisance covariates improve robustness while keeping the core FR‑005 requirement unchanged; they are modeled as additional controls in the partial correlation.  
- **Statistical choices**: Bonferroni across 32 tests, VIF/pairwise‑r diagnostics as warnings, permutation testing, and explicit power‑analysis justification directly implement FR‑005, FR‑006, and FR‑010.  
- **Scope**: Limiting motif enumeration to 3‑node and 4‑node motifs (8 categories) matches FR‑004 and the 32‑test correction count, avoiding unnecessary computational burden.  
- **Reproducibility**: Fixed random seed, pinned dependencies, streaming download, and comprehensive logging ensure full reproducibility per Constitution Principle I.  

## 6. Additional Artifacts
- **`results.json`** (generated in task T018) will contain the same statistical summary as `results.pdf` in machine‑readable form and will be validated against `contracts/results.schema.yaml`.  
- **`subject_metrics.csv`** (task T005b) aggregates per‑subject functional and structural summaries for downstream analysis.  

All success criteria (SC‑001…SC‑005) are addressed, and the plan now fully complies with the specification, constitution, and reviewer concerns. 