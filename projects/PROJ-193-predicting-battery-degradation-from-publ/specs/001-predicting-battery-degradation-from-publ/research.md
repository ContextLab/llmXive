# Research: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Feature**: `001-predict-battery-degradation`  
**Date**: 2026-10-25

## 1. Dataset Strategy

| Dataset | Source URL (verified) | Variables Available | Fit |
|---------|----------------------|--------------------|-----|
| **NASA Ames Battery Dataset** | https://data.nasa.gov/dataset/battery-cycling-data | Voltage, current, temperature time‑series; per‑cycle capacity; multiple protocols. | **OBTAINABLE** – programmatic CSV download via `datasets.load_dataset("nasa_ames/battery_cycling")` or direct HTTP fetch. |
| Battery Archive (original) | **No verified URL** – interactive portal only. | Voltage, current, temperature, capacity. | **UNOBTAINABLE** on CI; retained only for reference. |
| (Alternative open datasets) | See “# Verified datasets” block in the spec – none contain the required three electrochemical channels. | — | **NOT A FIT** |

**Conclusion**: The pipeline will use the NASA Ames Battery Dataset as the primary source, satisfying the applicable functional requirement with a verified, programmatically downloadable endpoint. The Battery Archive entry is retained only for documentation; the ingestion script will abort with a clear error if the NASA dataset is unavailable, preserving FR‑012.

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
| Power analysis | **CPU‑first** | `statsmodels` analytical calculation. |

No GPU escape hatch is required; all methods have faithful CPU implementations that respect the compute budget.

## 3. Statistical Rigor

- **Multiple comparisons**: Benjamini–Hochberg FDR correction applied to the five p‑values arising from the selected feature set (linear‑regression feature tests). The single Spearman correlation (SC‑008) is not defined in the spec and therefore omitted.
- **Power / sample‑size**: A post‑hoc power analysis is performed using `statsmodels.stats.power.FTestPower` to assess the ability to detect a ΔR² = 0.05 at α = 0.05 given the actual test‑set size. If achieved power < 0.8, the limitation is reported and ΔR² is presented with a 95 % confidence interval (methodology‑eecdef0d).  
- **Causal inference**: All claims are strictly **associational**; the data are observational. We perform a **protocol‑stratified sensitivity analysis** by reporting R², RMSE, and coverage separately for each protocol family, and by explicitly testing the unseen‑protocol subset. No causal language is used beyond “association”.  
- **Measurement validity**: Will be documented from NASA Ames metadata once the dataset is obtained.  
- **Collinearity**: VIF will be computed for the baseline incremental‑capacity features; no claims of independent effects are made.

## 4. Execution Plan Summary

The plan mirrors the phases described in `plan.md`:

1. **Scaffold** – pin dependencies, set up logging.  
2. **Ingestion & preprocessing** – download with retry ×3, checksum, filter, resample, leak‑free normalization, compute fade using **cycle 150** (or first > 100).  
3. **Model** – plain Bi‑LSTM (CPU) with an attention head (64 units per layer), Adam, early stopping, bounded hyper‑parameter sweep; defaults used if sweep exceeds 30 min.  
4. **Evaluation & Interpretation** – R²/RMSE on full test set and unseen‑protocol subset, MC‑dropout + **split‑conformal** intervals, power analysis for ΔR² = 0.05, SHAP, permutation importance, Integrated Gradients, **attention‑weight analysis**, feature aggregation, linear regression on top‑5 aggregated signatures, literature mapping.  
5. **Contracts & reporting** – validate against JSON‑Schema contracts, generate `results/predictions.json`, figures, and a concise evidence summary.

All artefacts are written to `data/processed/`, `models/`, and `results/` with provenance metadata; reproducibility is ensured by fixed seeds and deterministic pipelines.

### Key Adjustments Addressing Reviewer Feedback
- **Causal framing**: Explicitly labelled as associational; added protocol‑stratified sensitivity analysis.  
- **Confounder handling**: Protocol, chemistry, and manufacturer are used for stratified splits and reported per‑stratum.  
- **Target definition**: Uses capacity at **cycle 150** (or first > 100) to avoid any overlap with the predictor window, eliminating label leakage.  
- **Attention‑based attribution**: Implemented via an attention head and exported through `attention_attribution.py`.  
- **Feature‑selection constraint**: Enforced by `feature_selection.py` on the training subset only, with downstream regression evaluated on a distinct held‑out validation set.  
- **Power analysis**: Post‑hoc calculation with transparent reporting of achieved power.  

---



