# Research: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

**Feature**: `feat/001-crypto-regime-switching`  
**Date**: 2026-10-24  
**Spec**: [spec.md](../spec.md)

## Objective
Quantify how serial correlation and cross‑asset dependence between Bitcoin (BTC) and Ethereum (ETH) evolve across low‑volatility and high‑volatility regimes, and assess whether a Regime‑Switching VAR (RS‑VAR) yields a statistically superior fit to a stationary VAR.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first implementation** | All required libraries (`hmmlearn`, `statsmodels`, `datasets`, `requests`) run efficiently on CPU. Parallelised bootstrap uses the two CI cores; no GPU is needed, satisfying the compute‑feasibility clause. |
| **Open‑source data source (CoinGecko API)** | FR‑001 explicitly requires daily OHLCV data from the **CoinGecko public API** covering the most recent 5 years. The API is public, requires no key, and returns the necessary OHLC fields (and, via a secondary endpoint, volume). This satisfies the specification verbatim and avoids the unverified Hugging Face substitutes. |
| **Bootstrap likelihood‑ratio tests** | To avoid the Davies problem highlighted by reviewers, we replace asymptotic chi‑square LR tests with **parametric bootstrap** procedures (5 000 resamples for the HMM regime‑count test, 10 000 for the RS‑VAR vs stationary VAR test). This yields valid p‑values under the null. |
| **Independent regime‑distinctness validation** | In addition to the volatility proxy used as the HMM emission feature (squared returns), we compute a **10‑day rolling absolute‑return proxy**. A separate bootstrap LR test (5 000 resamples) checks that the identified regimes differ on this independent proxy, breaking circularity and satisfying SC‑009. |
| **Multiple‑testing correction** | Holm‑Bonferroni correction is applied to all hypothesis‑test p‑values (autocorrelation differences, cross‑asset correlation differences, LR tests) to control family‑wise error. |
| **Alternative volatility proxy** | In addition to squared returns, we compute a rolling standard deviation over a short‑term window. This satisfies FR‑007 and lets us compare regime definitions. |
| **Failure handling** | The notebook includes explicit `raise RuntimeError` messages for: missing columns, API download failures, HMM non‑convergence, singular covariance, duplicate timestamps. This directly addresses US‑3 acceptance scenarios. |
| **Runtime safeguard** | A wall‑time monitor aborts the bootstrap after 5 h and switches to a reduced 2 000‑sample bootstrap, logging the fallback. Guarantees compliance with SC‑007 (notebook runtime). |
| **Notebook location** | The entire pipeline lives in `notebooks/analysis.ipynb`, matching the Quickstart instructions and the Constitution Check table. |

## Dataset Strategy
| Role | Source URL | Loader / Method | Required Columns | Validation |
|------|------------|-----------------|------------------|------------|
| BTC daily OHLCV (raw) | `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1825` | Custom `download_ohlc(asset="bitcoin")` using `requests` → `pd.DataFrame` | `date, open, high, low, close` (volume merged from market chart endpoint) | Verified at runtime; aborts with clear error if any column missing. |
| ETH daily OHLCV (raw) | `https://api.coingecko.com/api/v3/coins/ethereum/ohlc?vs_currency=usd&days=1825` | Custom `download_ohlc(asset="ethereum")` using `requests` → `pd.DataFrame` | `date, open, high, low, close` (volume merged from market chart endpoint) | Same validation as BTC. |
| Auxiliary (volume) | `https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=usd&days=1825` | Same custom downloader merges `total_volume` into the OHLC table. | `volume` column added. | If volume cannot be merged, abort with informative message. |

*If either source ever ceases to provide the required fields, the notebook stops with a diagnostic, satisfying Constitution Principle VI (regime integrity) by preventing spurious regime inference on incomplete data.*

## Methodology Overview
1. **Download & checksum** raw BTC & ETH OHLCV files from CoinGecko, store under `data/raw/`. Compute SHA‑256 checksums and write `data/checksums.json`.  
2. **Preprocess**: parse `date` as `datetime64[ns]`, sort, drop duplicate timestamps (log count), ensure a continuous calendar (detect gaps > 5 consecutive missing days → abort).  
3. **Log‑returns**: `r_t = log(close_t / close_{t‑1})` for each asset.  
4. **Volatility proxies**: (a) squared returns (`vol_sq`), (b) 10‑day rolling standard deviation (`vol_roll_std`), (c) 10‑day rolling absolute‑return mean (`vol_abs_10d`) – used only for independent regime validation.  
5. **HMM fitting**: `GaussianHMM(n_components=2, covariance_type="full", n_iter=100, tol=1e-4)` on `[btc_ret, eth_ret, vol_sq]`.  
6. **Bootstrap LR for regime count**: 5 000 resamples comparing log‑likelihood of 1‑state vs 2‑state HMM; p < 0.05 required (FR‑010, SC‑009).  
7. **Independent regime‑distinctness validation**: Using the *independent* proxy `vol_abs_10d`, perform a second bootstrap LR (5 000 resamples) to confirm that the two regimes differ significantly on this metric (breaks circularity).  
8. **Assign regime labels** → `regime_labels.csv`.  
9. **Stationarity check**: Augmented Dickey‑Fuller test per regime on each return series; if a series fails to reject the unit‑root null at α = 0.05, a warning is logged and the series is differenced before VAR fitting.  
10. **Regime‑Switching VAR**: For each regime, fit `statsmodels.tsa.VAR` with lag‑1 (selected by AIC/BIC). Extract:  
    - Lag‑1 autocorrelation for BTC & ETH (diagonal of AR(1) matrix).  
    - Pearson correlation of residuals between assets.  
11. **Bootstrap difference test** (2 000 resamples) for autocorrelation differences across regimes; Holm‑Bonferroni correction → **SC‑004**.  
12. **Permutation Fisher‑z test** for cross‑asset residual correlation differences; Holm‑Bonferroni correction → **SC‑005** (or absolute Δ ≥ 0.20).  
13. **Baseline stationary VAR** on the full series.  
14. **Bootstrap LR (10 000 resamples)** comparing RS‑VAR vs stationary VAR; runtime guard may reduce to 2 000 resamples, logged. → **SC‑003**.  
15. **Alternative models**: (a) 3‑state RS‑VAR, (b) RS‑VAR with `vol_roll_std` proxy. Compute BIC for each; ΔBIC ≤ 2 indicates no meaningful improvement → **SC‑006**.  
16. **Multiple‑testing correction**: Holm‑Bonferroni applied to all p‑values from steps 11‑14.  
17. **Generate outputs**:  
    - Tables (`results/tables/`).  
    - Figures (`results/figures/`): ACF per regime, cross‑asset correlation heatmaps, BIC comparison plot, LR‑test histogram.  
    - Log file `analysis.log` with timestamps for every major step.  
18. **Contract validation**: `pytest -q tests/contract/` validates raw price files, regime labels, and RS‑VAR output against the schemas in `contracts/`.  

All steps are encapsulated in `notebooks/analysis.ipynb`, executed in CI via `papermill`. The notebook is deterministic (seeds pinned) and fully reproducible.

## Expected Deliverables
- `notebooks/analysis.ipynb` (single notebook pipeline)  
- CSV/JSON artefacts: `regime_labels.csv`, `rsvart_stats.csv`, `comparison_metrics.csv`, `rsvart_output_regime_*.json`  
- Figures (PNG): `acf_by_regime.png`, `cross_corr_heatmap.png`, `bic_comparison.png`, `lr_bootstrap_hist.png`  
- Log file `analysis.log` (timestamped)  
- Contract test report `test_report.xml`  

---


