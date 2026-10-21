# Research: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Research Question
Do waking‑state network centrality metrics (degree, betweenness, eigenvector) predict the magnitude of neural synchrony (Phase‑Locking Index, PLV) observed during each sleep stage (N1, N2, N3, REM), after accounting for age, gender, total sleep time, and any additional available metadata (e.g., medication, sleep quality)?

## Methodological Approach

### 1. Data Acquisition & Preprocessing
| Item | Details |
|------|---------|
| **Source** | PhysioNet Sleep‑EDF (Hugging Face mirror) |
| **Verified URL** | `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` |
| **Inclusion Criteria** | • ≥ 2 min continuous, artifact‑free waking segment.<br>• At least one annotated epoch for each sleep stage (N‑stage, REM).<br>• Presence of EEG (Fpz‑Cz, Pz‑Oz) **and** auxiliary channels (EOG, EMG) to construct a multi‑node network (peripheral channels used only in a secondary sensitivity analysis). |
| **Filtering** | Band‑pass spanning the lower bound of the target frequency range to 45 Hz (SciPy FIR, zero‑phase). |
| **Artifact Removal** | ICA via MNE; reject components with kurtosis > 5.0 **or** high‑frequency power > 3 × baseline (0.5–2 Hz median power). |
| **Epoching** | Non‑overlapping 30 s windows (epoch length = 30 s, source 1908.11463). |
| **Night‑ID Extraction** | EDF header date used to create `waking_night_id` and `sleep_night_id`. |

### 2. Waking Functional Connectivity
- **Bands**: Theta (4–8 Hz) and Alpha (8–13 Hz).  
- **Metric**: Magnitude‑squared coherence (Welch’s method, Hann window).  
- **Output**: Symmetric coherence matrices (`0 < value < 1`) for each band per subject.

### 3. Network Centrality
- **Primary Graph Construction**: Nodes = EEG channels only (Fpz‑Cz, Pz‑Oz). Edge weights = coherence values.  
- **Secondary Sensitivity Graph**: Optional inclusion of EOG and EMG channels (`--include-peripheral` flag).  
- **Metrics** (NetworkX): degree, betweenness, eigenvector centrality.  
- **Aggregation**: Mean across nodes → per‑subject centrality vector (degree_mean, betweenness_mean, eigenvector_mean).

### 4. Centrality Stability Validation
- **Within‑Waking Split‑Half**: The waking segment is split into two equal halves (when ≥ 2 min). Centrality metrics are recomputed on each half and ICC (two‑way mixed effects) is calculated across halves for each metric.  
- **Cross‑State Stability**: Centrality is also computed on a stable sleep stage (N2) using the same coherence‑based graph (EEG‑only). An ICC between the waking‑segment centrality and the N2‑stage centrality is calculated per subject.  
- ICC < 0.6 is flagged as “unstable” and reported (SC‑006, SC‑008).

### 5. Sleep‑Stage Neural Synchrony
- **Metric**: Phase‑Locking Value (PLV) computed across all channel pairs per epoch (MNE).  
- **Aggregation**: Mean global PLV per sleep stage per subject (float ∈ [0, 1]).

### 6. Aggregation & Validation
- Combine centrality means and stage‑wise PLVs into `SubjectMetrics.csv` (one row per subject per stage).  
- Validate against `contracts/dataset.schema.yaml`.  

### 7. Collinearity Diagnostics
- Compute global Variance Inflation Factor (VIF) for the three centrality predictors across subjects.  
- Flag any VIF > 5.0 (reported in the final JSON and Markdown).  

### 8. Sample‑Size Verification
- After filtering, require **N ≥ 30** subjects with ≥ 2 min clean wake.  
- If not met, pipeline aborts and logs “Insufficient Sample Size”.  

### 9. Normality Testing & Correlation Selection
- Shapiro‑Wilk test on each variable pair (SciPy).  
- **Pearson** if both p ≥ 0.05; otherwise **Spearman**.  

### 10. Covariate Adjustment
- Partial correlation controlling for age, gender, total sleep time, **and any additional metadata fields present** (e.g., medication, sleep quality) using `statsmodels`.  
- Missing covariates → fallback to bivariate correlation with a flag.  

### 11. Correlation Analysis
- **Tests**: 3 centrality metrics × 4 sleep stages × 2 bands = **24** primary tests; plus 6 auxiliary partial‑correlation tests (age, gender, total sleep time) → total **30** tests (as defined in FR‑006).  
- Compute coefficient, raw *p*, and store method used.  

### 12. Multiple‑Comparison Control
- Bonferroni correction across all planned tests (`p_corrected = min(p_raw * 30, 1.0)`).  

### 13. Power Assessment (Post‑hoc)
- Using `statsmodels.stats.power`, compute achieved power for the observed effect sizes given N = 30 and Bonferroni‑adjusted α.  
- Power results are reported in the final Markdown; low power is explicitly discussed as a limitation (SC‑007).  

### 14. Reporting
- JSON (`analysis_results.json`) with full statistics.  
- Markdown (`report.md`) containing:  
  - Dataset description & filtering summary.  
  - Table of results (highlighting `p_corrected < 0.05`).  
  - **Confounding Limitation**: flag subjects where `waking_night_id == sleep_night_id`.  
  - **VIF Diagnostics**: global VIF values and interpretation.  
  - **Centrality Stability**: split‑half ICC values and cross‑state ICC values, with flags for instability.  
  - **Power Discussion**: post‑hoc power estimates and caveats.  
  - **Causal Disclaimer**: all findings are associational.  

## Dataset Strategy

| Dataset | Description | Verified URL | Fit Verification |
|---------|-------------|--------------|------------------|
| **PhysioNet Sleep‑EDF** (Hugging  Face mirror) | Polysomnographic EEG (Fpz‑Cz, Pz‑Oz) with EOG/EMG, sleep‑stage annotations, and brief pre‑sleep wake. | `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` | Contains required EEG/EOG/EMG channels, sleep‑stage labels, and wake segments. Wake ≥ 2 min is enforced; if insufficient subjects remain, the pipeline aborts (transparent limitation). |

**Decision/Rationale**: The mirror provides programmatic download, checksum verification, and all necessary signals. EEG‑only centrality preserves neural construct validity; peripheral channels are retained for a secondary sensitivity analysis only.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni (α = 0.05).  
- **Power**: Minimum N ≥ 30 enforced; post‑hoc power analysis acknowledges limited power.  
- **Observational Design**: No randomization; all statements are correlational.  
- **Collinearity**: Global VIF computed; VIF > 5.0 flagged.  
- **Missing Sleep Stages**: Excluded from the specific correlation; no imputation.  
- **Data Corruption**: Corrupted EDF files are logged, skipped, and do not stop the run.  
- **Temporal Confounding**: Same‑night waking/sleep flagged in report.  
- **Normality**: Shapiro‑Wilk determines Pearson vs. Spearman (internal to FR‑006).  
- **Covariate Adjustment**: Partial correlations control for age, gender, total sleep time, and any extra metadata when available.  

## Limitations
1. **Wake Duration** – The ≥ 2 min wake filter may reduce usable subjects; this is reported transparently and may limit power.  
2. **Channel Set** – Primary centrality uses only EEG channels to preserve neural interpretability; peripheral‑channel results are provided as a sensitivity check.  
3. **Sample Size** – If fewer than 30 subjects survive filtering, the study is under‑powered; the pipeline aborts with a clear warning.  
4. **Stability** – Split‑half ICC and cross‑state ICC values may be low for some subjects, indicating instability of the predictor; flagged results are discussed.  
5. **Observational Nature** – No causal inference; all findings are associational.  

---



