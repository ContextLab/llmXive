# Research: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

**Feature**: `feat/001-crypto-regime-switching`  
**Date**: 2026-10-23  
**Spec**: [spec.md](../spec.md)

## Objective
Quantify how serial correlation and cross‑asset dependence between Bitcoin (BTC) and Ethereum (ETH) evolve across low‑volatility and high‑volatility regimes, and evaluate whether a Regime‑Switching VAR (RS‑VAR) provides a statistically superior fit to a stationary VAR.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first implementation** | All required libraries (`hmmlearn`, `statsmodels`, `pandas`) have efficient CPU implementations. The bootstrap procedures are parallelized across the two available CI cores. No GPU is needed, satisfying the compute‑feasibility clause. |
| **Open‑source data source: CoinGecko API** | The specification mandates downloading OHLCV data; CoinGecko’s public API is openly accessible, requires no key, and returns the required columns. This satisfies Constitution Principle II without relying on unverified HuggingFace datasets. |
| **Data‑validation gate** | After download, the notebook checks for the six required OHLCV columns. Missing columns trigger a clear abort (`RuntimeError: Required OHLCV columns missing in <asset>`), fulfilling US‑3. |
| **Bootstrap over asymptotic LR** | To avoid the Davies problem for LR tests comparing RS‑VAR to a stationary VAR, we use a **parametric bootstrap** (10 000 resamples) for the VAR LR test and a 5 000‑resample bootstrap LR for the HMM regime test (FR‑010/SC‑009). The bootstrap is implemented with a fully vectorized NumPy routine and `joblib.Parallel` across the two CI cores. A runtime guard aborts after 5 hours and automatically falls back to **2 000 resamples**, logging the fallback and noting the limitation. |
| **Alternative volatility proxy** | To satisfy FR‑007 we compute both (a) squared daily returns (baseline) and (b) a 10‑day rolling standard deviation. This allows a direct comparison of regime definitions. |
| **Model‑selection criteria** | BIC is computed for all candidate models (2‑state RS‑VAR, 3‑state RS‑VAR, stationary VAR). ΔBIC ≤ 2 is the threshold for SC‑006. |
| **Failure handling** | Edge‑case behaviours (API failure, HMM non‑convergence, singular covariance) are coded as explicit `raise RuntimeError` with clear messages, matching US‑3 acceptance scenarios. |
| **Bootstrap runtime safeguard** | Because a full 10 000‑sample bootstrap can approach the CI time limit, the notebook monitors elapsed wall‑time. If the VAR LR bootstrap exceeds 5 hours, it aborts the remaining resamples and re‑runs a reduced 2 000‑sample bootstrap, recording the fallback in `analysis.log`. This ensures the job completes within the free‑tier budget while still providing a statistically meaningful test (albeit with reduced precision). |

## Dataset Strategy
| Role | Source | Loader | Required Columns | Validation Outcome |
|------|--------|--------|------------------|--------------------|
| BTC daily OHLCV (raw) | CoinGecko public API (`) | Custom `requests` call → `pd.DataFrame` | `date, open, high, low, close, volume` | Verified at runtime; aborts if any column missing. |
| ETH daily OHLCV (raw) | CoinGecko public API (`) | Custom `requests` call → `pd.DataFrame` | `date, open, high, low, close, volume` | Verified at runtime; aborts if any column missing. |
| Auxiliary (optional) | None | – | – | No substitute; if required columns are absent, the analysis aborts and the study is re‑scoped. |

*If the CoinGecko API ever fails to provide the required OHLCV fields, the notebook will terminate with a clear diagnostic (see Phase 0). This satisfies Constitution Principle VI (regime integrity) by preventing spurious regime inference on incomplete data.*

## Methodology Overview
1. **Download & checksum** raw BTC & ETH files; store under `data/raw/`.  
2. **Preprocess**: parse dates, sort, drop duplicates (log count), forward‑fill missing days (if any) – abort if > 5 consecutive missing days (US‑3).  
3. **Compute log‑returns**: `r_t = log(close_t / close_{t-1})`.  
4. **Construct volatility proxies**: (a) squared returns, (b) 10‑day rolling standard deviation.  
5. **Fit HMM** (`GaussianHMM` with 2 components) on the joint vector `[btc_ret, eth_ret, volatility_proxy]`.  
6. **Bootstrap LR test** (5 000 resamples) for 1‑ vs 2‑state HMM (FR‑010).  
7. **Assign regime labels** to each day; save `regime_labels.csv`.  
8. **ADF test** per regime on log‑returns; if non‑stationary, issue warning and optionally difference the series.  
9. **Fit RS‑VAR** per regime (`statsmodels.tsa.VAR`) allowing regime‑specific coefficient matrices and error covariances.  
10. **Extract lag‑1 autocorrelation** (diagonal of AR(1) matrix) and **cross‑asset residual correlation** (Pearson on residuals).  
11. **Bootstrap difference test** (2 000 resamples) for autocorrelation differences across regimes (SC‑004); Holm‑Bonferroni correction applied.  
12. **Permutation Fisher‑z test** for cross‑asset correlation differences (SC‑005); Holm‑Bonferroni corrected.  
13. **Fit baseline stationary VAR** on the full series.  
14. **Bootstrap LR test** (10 000 resamples) comparing RS‑VAR vs stationary VAR (FR‑005). Runtime guard may reduce to 2 000 if needed (see Decision/Rationale).  
15. **Fit alternative 3‑state RS‑VAR** and RS‑VAR with rolling‑std volatility proxy; compute BIC for each (FR‑007).  
16. **Multiple‑testing correction** applied across all p‑values (Holm‑Bonferroni).  
17. **Generate tables & figures**: regime‑specific coefficient tables, correlation heatmaps, BIC comparison plot, LR‑test histograms.  
18. **Log** every major step with timestamps to `analysis.log`.  
19. **Validate outputs** against YAML schemas in `contracts/` via `pytest`.  

All steps are encapsulated in a single Jupyter notebook (`analysis.ipynb`) that can be executed with `papermill` in CI.

## Expected Deliverables
- `analysis.ipynb` (executable end‑to‑end pipeline)  
- CSV tables: `regime_labels.csv`, `rsvart_stats.csv`, `comparison_metrics.csv`  
- Figures (PNG): `acf_by_regime.png`, `cross_corr_heatmap.png`, `bic_comparison.png`  
- Log file `analysis.log` with timestamps.  
- Contract validation report (`test_report.xml`).  

---

