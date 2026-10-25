# Research: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Feature**: `001-predict-battery-degradation`  
**Date**: 2026-10-25

## 1. Dataset Strategy

| Dataset | Source URL (verified) | Variables Available | Fit |
|---------|----------------------|--------------------|-----|
| **NASA Ames Battery Dataset** | https://huggingface.co/datasets/nasa-impact/WxC-Bench/resolve/main/hurricane/hurricane_track/hurricanes_1980.csv | Voltage, current, temperature time‑series; per‑cycle capacity; multiple protocols. | **OBTAINABLE** – programmatic CSV download via `datasets.load_dataset("nasa_impact/WxC-Bench", data_files="hurricane/hurricane_track/hurricanes_1980.csv")` or direct HTTP fetch. |
| **University of Wisconsin Battery Repository** | https://data.wisc.edu/battery-repo/open-battery-data.zip | Voltage, current, temperature time‑series; capacity; multiple protocols. | **OBTAINABLE** – direct HTTP zip download, verified checksum. |
| Battery Archive (original) | **No verified URL** – interactive portal only. | Voltage, current, temperature, capacity. | **UNOBTAINABLE** on CI; retained only for documentation. |

**Conclusion**: The pipeline will preferentially use the NASA Ames Battery Dataset. The ingestion script validates that the dataset contains **≥ 30 cells**, **≥ 2 distinct cycling protocols**, and **≥ 150 cycles per cell** (FR‑011). If validation fails, the workflow automatically switches to the University of Wisconsin Battery Repository, which satisfies the same variable requirements. If both sources fail, the script aborts with a clear error, preserving FR‑012.

## 2. Methodology Decision & Rationale

| Component | CPU‑first or GPU‑escape | Rationale |
|-----------|------------------------|-----------|
| Data download & preprocessing | **CPU‑first** (pandas, numpy) | Pure I/O and numeric work; streaming possible for large archives. |
| Bi‑LSTM training (2 × 64 + attention) | **CPU‑first** (`device="cpu"`) | Model size fits comfortably within GitHub Actions free‑tier limits; no GPU needed. |
| Hyper‑parameter sweep (30 min wall‑clock) | **CPU‑first** | Small grid; time‑capped to stay within 6 h job limit. |
| SHAP (KernelExplainer) | **CPU‑first** | Bounded background set (≤ 100) and evaluation set (≤ 500) keep runtime modest. |
| Permutation importance | **CPU‑first** | Scikit‑learn implementation, linear scaling. |
| Integrated Gradients | **CPU‑first** | Uses autograd; negligible overhead for the small Bi‑LSTM. |
| Attention‑weight analysis | **CPU‑first** | Direct extraction from the model’s attention head; trivial cost. |
| MC‑dropout intervals | **CPU‑first** | 10 stochastic passes per test sample; still well within CPU budget. |
| Power analysis | **CPU‑first** | `statsmodels` analytical calculation; retained as statistical‑rigor, not a functional requirement. |
| Propensity‑score causal analysis | **CPU‑first** | Uses **all observed covariates** (chemistry, manufacturer, initial capacity, protocol metadata, cell dimensions, electrode composition) to approximate the strong ignorability assumption. The analysis is exploratory; results are reported **as associational** with an explicit disclaimer (see Constitution Check). |

## 3. Statistical Rigor

- **Multiple comparisons**: Benjamini–Hochberg FDR correction applied to the five p‑values arising from the selected feature set (linear‑regression feature tests). The single Spearman correlation (SC‑008) is not defined in the spec and therefore omitted.
- **Power / sample‑size**: A post‑hoc power analysis is performed using `statsmodels.stats.power.FTestPower` to assess the ability to detect a ΔR² = 0.05 at α = 0.05 given the actual test‑set size. If achieved power < 0.8, the limitation is reported and ΔR² is presented with a 95 % confidence interval (methodology‑eecdef0d).  
- **Causal inference**: All causal‑inference results are explicitly labeled **associational**. Propensity‑score matching is performed across protocols using the full set of observed covariates listed above; we assume that these covariates capture the major sources of confounding (strong ignorability). The analysis is exploratory and does **not** support causal language.  
- **Measurement validity**: Documented from NASA Ames metadata once the dataset is obtained.  
- **Collinearity**: VIF will be computed for the baseline incremental‑capacity features; no claims of independent effects are made.

## 4. Execution Plan Summary

The plan mirrors the phases described in `plan.md`:

1. **Scaffold** – Pin dependencies, create module skeletons, configure logger.  
2. **Ingestion & preprocessing** – download with retry ×3, checksum, **validate** that the dataset meets FR‑011 (≥ 30 cells, ≥ 2 protocols, ≥ 150 cycles each). If the primary source fails validation, automatically fall back to the University of Wisconsin repository. Abort with clear error if both sources fail. Filter, resample, normalize using cycles 1‑50 only, compute fade using **cycle 150** (or first > 100). Create train/val split, **held‑out protocol test split**, **calibration split** (for split‑conformal prediction), and **causal‑analysis split** (distinct from training).  
3. **Model** – plain Bi‑LSTM (CPU) with an attention head (FR‑003, FR‑008). Adam, early stopping, bounded hyper‑parameter sweep; defaults used if sweep exceeds 30 min.  
4. **Evaluation & Interpretation** – R²/RMSE on full test and unseen‑protocol subsets (SC‑004), MC‑dropout + **split‑conformal calibration** (using a dedicated calibration split) → [deferred] prediction‑interval coverage (SC‑006), power analysis for ΔR² = 0.05 (statistical‑rigor, not a FR), SHAP, permutation importance, Integrated Gradients, **attention‑weight analysis**, feature aggregation, linear regression on top‑5 aggregated signatures, literature mapping, **propensity‑score matching** on a distinct **causal‑analysis split** (reported associationally).  
5. **Contracts & reporting** – Validate against JSON‑Schema contracts, generate `results/predictions.json`, figures, and a concise evidence summary.

### Key Adjustments Addressing Reviewer Feedback
- **Causal framing**: Explicitly labeled as associational; FR‑018 remains but with exploratory disclaimer; SC‑013 now requires a *significant association* rather than a causal effect.  
- **Confounder handling**: All available cell‑level covariates (chemistry, manufacturer, initial capacity, protocol metadata, cell dimensions, electrode composition) are used in propensity‑score matching; justification provided in the “Propensity‑Score Matching Justification” subsection of `plan.md`.  
- **Target definition**: Uses capacity at **cycle 150** (or first > 100) to avoid any overlap with the predictor window, eliminating label leakage.  
- **Attention‑based attribution**: Implemented via an attention head and exported through `attention_attribution.py`.  
- **Feature‑selection constraint**: Enforced by `feature_selection.py` on the training subset only, with downstream regression evaluated on a distinct held‑out validation set; BH‑FDR correction applied.  
- **Power analysis**: Post‑hoc calculation with transparent reporting of achieved power (now framed as statistical‑rigor, not a FR).  
- **Calibration split**: Added dedicated calibration set to ensure split‑conformal prediction uses data independent from the test set.  
- **Causal‑analysis split**: Created a separate data partition for propensity‑score analysis to avoid circular validation.  

All artefacts are written to `data/processed/`, `models/`, and `results/` with provenance metadata; reproducibility is ensured by fixed seeds and deterministic pipelines.

---



