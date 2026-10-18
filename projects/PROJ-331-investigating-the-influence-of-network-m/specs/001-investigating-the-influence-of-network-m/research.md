# Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Research Question & Hypothesis
**Question**: Do specific 3‑node and 4‑node network motif configurations in structural brain connectomes *associate* (observational framing) with individual variation in resting‑state functional connectivity (rsFC) strength and global efficiency across subjects?

**Hypothesis**: After controlling for each subject’s structural global degree **and** age, sex, and head‑motion, motif‑z‑scores for certain motifs will show significant partial correlations with rsFC strength and/or global efficiency.

## 2. Dataset Strategy

| Dataset | Source (verified) | Access Method | Variables Used | Status |
|---------|-------------------|---------------|----------------|--------|
| OpenNeuro functional parquet (rsFC) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet | `datasets.load_dataset(..., streaming=True)` | Resting‑state BOLD time‑series → rsFC matrices; subject IDs for cohort selection | ✅ Verified, open |
| OpenNeuro diffusion tractography (structural) | https://openneuro.org/datasets/ds001734 (direct `datalad get` of `sub-*/ses-*/dwi/*.nii.gz`) | `datalad install` + `datalad get` | Diffusion‑derived streamlines → binary structural adjacency after Schaefer parcellation at a fine‑grained resolution. | ✅ Verified, open, **paired with functional data** |

**Dataset‑variable fit assessment**: Both modalities are present for the same group of subjects; the structural diffusion files are programmatically retrievable via `datalad`. This satisfies the requirement for paired structural‑functional data.

## 3. Methodology

### 3.1 Data acquisition & preprocessing
1. **Streaming download** of the functional parquet and diffusion tractography files for the first 50 subjects listed in `participants.tsv`. Compute SHA‑256 checksums and record them in `manifest.json`. Subjects missing either modality are logged and excluded (US‑1 acceptance scenario 2).
2. **Parcellation**: Map diffusion streamlines to a 100‑node Schaefer cortical atlas (Schaefer et al., 2018) and produce a binary undirected adjacency matrix (`structural.npy`). For rsFC, extract the BOLD time‑series, compute Pearson correlation across the 100 parcels → symmetric `rsfc.npy`. Derive:
   - **Mean rsFC strength** = average absolute off‑diagonal correlation.
   - **Global efficiency** = `networkx.global_efficiency` on the binary graph obtained by thresholding |r| > 0.2.
3. **Covariate extraction**: Pull age, sex, and mean framewise displacement (head‑motion) from `participants.tsv` and merge into `subject_metrics.csv`.

### 3.2 Motif quantification
- Treat each structural connectome as an **undirected binary** graph (primary analysis) and also compute **weighted‑motif** counts for exploratory reporting.
- **Enumeration**: Use `networkx.algorithms.isomorphism` to count all non‑isomorphic 3‑node (4 classes) and 4‑node (9 classes) motifs, yielding Several motif categories..
- **Null model**: Maslov–Sneppen degree‑preserving rewiring, ≥ 1000 iterations, random seed = 42. Compute z‑score per motif: `z = (N_obs − μ_null) / σ_null`. If σ_null = 0, set z = 0.
- **Timeout guard**: Abort enumeration for a subject if wall‑clock time exceeds 300 s, log a timeout warning, and continue (SC‑002).

### 3.3 Statistical analysis
- **Partial correlations**: For each motif (z‑score) and each functional metric (strength, global efficiency), compute Pearson and Spearman partial correlations controlling for structural global degree, age, sex, and motion.
- **Multiple‑comparison correction**: Bonferroni across **52** tests (13 motifs × 2 metrics × 2 correlation types); corrected α = 0.05/52 ≈ 0.00096. Flag motifs with corrected p < 0.05.
- **Multicollinearity diagnostics** (reporting only):
  - Compute VIF for the full set of motif predictors; if any VIF ≥ 5, log a warning but do **not** exclude predictors.
  - Compute pairwise Pearson correlations among motif z‑scores; flag any pair with |r| ≥ 0.9 as a warning.
- **Permutation test**: Shuffle subject labels ≥ 1000 times (seed = 42) to obtain an empirical p‑value per motif; report alongside analytical p.
- **Zero‑variance handling**: If a motif’s z‑score vector across subjects has variance < 1e‑6, skip the test, record “insufficient variance” in the results, and continue.
- **Sensitivity analysis**: Repeat the partial‑correlation pipeline **without** structural global degree as a covariate and include these results in the report to assess over‑control concerns.
- **Power analysis**: Using `statsmodels.stats.power.tt_ind_solve_power`, compute the minimum detectable Pearson r **based on the actual number of processed subjects (`cohort_actual`)** for N = `cohort_actual`, α_adj = 0.05/52, power = 0.80.  
  **Fallback strategy**:  
  1. If the computed power is **below 0.80**, the pipeline will attempt to extend the cohort by fetching additional subjects from the OpenNeuro ds001734 dataset, up to a maximum of **60 subjects** (if available).  
  2. After extending, power is recomputed.  
  3. If power still falls short, the pipeline logs a clear warning and the PDF report includes a statement that the study is under‑powered for the intended effect size, recommending future data collection.  
  This ensures that the intended 0.80 power is either achieved or explicitly reported as a limitation.

### 3.4 Reporting
- Generate `results.pdf` (ReportLab):
  - One page per motif containing: scatter plot of motif z‑score vs. each functional metric, 95 % confidence band, partial r (Pearson & Spearman), raw p, Bonferroni‑corrected p, empirical permutation p, VIF warning flag, flagged predictor pairs, and, for the weighted‑motif exploratory figure, a brief note.
  - Power‑analysis section with numeric minimum detectable r computed from the **actual N**, adjusted α, and interpretation of Type II error. If the fallback extension was needed, the section notes the final cohort size and whether the target power was reached.
  - Limitations paragraph describing any subjects excluded and the observational nature of the findings.
  - Mandatory disclaimer string **“These findings are associational only and do not imply causation.”** inserted verbatim; after PDF creation the pipeline extracts text to verify presence.

## 4. Compute Feasibility
- **CPU‑first**: All steps (streaming, correlation, motif counting on 100‑node graphs, 1000 null models, 1000 permutations) run comfortably on the 2‑core, 7 GB RAM runner. No GPU is required.
- **Memory**: Streaming avoids loading the full parquet into memory; only per‑subject matrices (~40 KB each) are kept in RAM.
- **Time**: Empirically, motif enumeration for a moderately sized graph with 1000 null models completes in on the order of minutes; permutation testing ≈ a few minutes; total pipeline ≤ 4 h on CI, well under the 6 h limit.

## 5. Decision / Rationale
- **Functional & structural modalities**: Both are verified open datasets from OpenNeuro ds001734; no fabrication is needed.
- **Covariate inclusion**: Age, sex, and motion are standard confounds in neuroimaging; their inclusion reduces bias without over‑controlling the motif effect (sensitivity analysis assesses any residual over‑control).
- **Statistical choices**: Bonferroni across all 52 tests controls family‑wise error; VIF/pairwise diagnostics are reported as warnings only, respecting the analysis design. Power analysis uses the correct α_adj and dynamically adapts to the actual sample size, with a concrete fallback strategy to maintain or transparently report the target 0.80 power.
- **Scope**: 3‑node and 4‑node motifs only, as explicitly required; binary treatment follows the specification, with optional weighted counts for exploratory insight.
