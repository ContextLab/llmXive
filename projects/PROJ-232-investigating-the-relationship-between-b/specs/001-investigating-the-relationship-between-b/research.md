# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Research Question
*Exploratory Primary*: **Can resting‑state functional‑connectivity network metrics predict any available music‑related behavioral proxy** (e.g., `music_emotion_score`) present in the verified HCP parquet collection?  
*Original (unavailable)*: Predict BMRQ total scores. Since BMRQ is not present in any open dataset, the original hypothesis cannot be tested; this limitation is documented in the Data‑Gap Report. The proxy is used **only for exploratory analysis** and is **not assumed** to measure the same construct (musical reward sensitivity) as the validated BMRQ.

## Construct Validity Disclaimer
The optional `behavioral_proxy` column (if present) is **not** a validated measure of musical reward sensitivity. It may capture related but distinct aspects of music‑related behavior. Consequently, any significant associations reported are **exploratory** and should not be interpreted as evidence that resting‑state network dynamics predict the BMRQ construct. Future work should replicate findings with a formally validated musical emotion or reward questionnaire.

## Dataset Strategy

### Verified Datasets
| Dataset | URL(s) | Contents | Status |
|---|---|---|---|
| **HCP Parquet Collection** | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet` <br> `https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv` <br> `https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | Demographics (`subject_id`, `age`, `sex`), motion metric (`fd_mean`), and pre‑computed functional‑connectivity vectors (`fc_upper_tri`). May contain an optional music‑related column (e.g., `music_emotion_score`). No BMRQ column. | **VERIFIED** |
| **BMRQ** | *No verified source* | Budapest Music Reward Questionnaire total scores. | **UNVERIFIED** – cannot be fetched programmatically. |

### Variable Mapping & Feasibility

| Required Variable (Spec) | Presence in Verified Dataset | Action |
|---|---|---|
| `subject_id` | ✅ | Use as primary key. |
| `age` | ✅ | Covariate for partial correlation. |
| `sex` | ✅ | Covariate. |
| `fd_mean` | ✅ | Covariate (motion). |
| `BMRQ total` | ❌ (absent; no verified source) | Generate **Data‑Gap Report**; primary BMRQ hypothesis is **not** tested. |
| `alternative music‑related score` (e.g., `music_emotion_score`) | *Conditional* – present only if the parquet files contain such a column. | If present, run **exploratory** analysis; otherwise skip behavioral modeling. |
| `functional connectivity matrix` | ✅ (reconstructed from `fc_upper_tri`) | Proceed with graph‑metric calculations. |

**Conclusion**: Because the BMRQ variable is unavailable, the study proceeds **only** if an alternative music‑related proxy exists; otherwise the pipeline stops after Phase 0 with a Data‑Gap Report.

## Statistical Rigor & Methodology

| Aspect | Method | Details |
|---|---|---|
| **Multiple‑Comparison Correction** | Benjamini‑Hochberg FDR | Applied to all metric‑wise partial correlations (global + 3 network‑specific + edge‑level set). Threshold `q < 0.05`. |
| **Sample‑Size & Power** | `statsmodels.stats.power.CorrelationPower` | Target effect size `r ≥ 0.20`, α = 0.05. Achieved power is computed **per metric** and stored in the `power_achieved` column of `analysis_results.csv`. |
| **Causal Inference** | Observational | All statements are **associational**; no causal claims are made. |
| **Measurement Validity** | The proxy variable (if any) is **not** the validated BMRQ; its construct validity is limited. This limitation is explicitly reported and results are treated as exploratory. |
| **Collinearity** | Variance Inflation Factor (VIF) | Predictors with VIF > 5 are removed before regression; VIF values are logged in `results/vif_report.json`. |

## Compute Feasibility

- **CPU‑First**: All steps (download, matrix reconstruction, graph metrics, regression) run comfortably within the 7 GB RAM limit on the GitHub Actions free tier.  
- **GPU Escape Hatch**: Not required.  

## Decision Rationale

1. **Dataset Choice** – The HCP parquet collection is the only *verified* open source that supplies both demographics and pre‑computed connectivity features.  
2. **BMRQ Absence** – No verified BMRQ source exists; the primary hypothesis therefore cannot be tested. The pipeline detects this early and aborts, avoiding wasted compute.  
3. **Exploratory Path** – If a music‑related proxy is present, the same analytical workflow can be reused, preserving most of the intended scientific workflow while being transparent about construct‑validity limits.  
4. **Statistical Choices** – FDR correction and VIF checks ensure robustness given the high dimensionality of edge‑level features.  

## Limitations

- **Primary behavioral measure missing** → The original hypothesis (BMRQ prediction) cannot be evaluated without a scope revision.  
- **No raw fMRI** → fMRIPrep preprocessing is omitted; we rely on already‑derived connectivity vectors.  
- **Power** – Sample size is limited to the number of subjects present in the parquet files (a modest number of participants). If `N < 80`, power to detect `r = 0.20` may fall below 0.80; this will be reported per metric.  
- **Exploratory nature** – Findings based on a proxy behavioral variable are preliminary and should be interpreted cautiously.  

---



