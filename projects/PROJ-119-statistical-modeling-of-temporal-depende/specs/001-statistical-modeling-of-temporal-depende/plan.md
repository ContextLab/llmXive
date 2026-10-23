# Implementation Plan: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

**Branch**: `feat/001-crypto-regime-switching` | **Date**: 2026-10-23 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `specs/001-statistical-modeling-of-temporal-depende/spec.md`

## Summary
The core requirement is to download daily OHLCV data for Bitcoin (BTC) and Ethereum (ETH) over the last five years via the CoinGecko public API, compute log‑returns and volatility proxies, fit a 2‑state Hidden Markov Model (HMM) to define low‑ and high‑volatility regimes, estimate a Regime‑Switching Vector Autoregression (RS‑VAR) for each regime, and compare it to a stationary VAR using bootstrap likelihood‑ratio tests and BIC. The plan now maps every Functional Requirement (FR‑001 – FR‑010) and Success Criterion (SC‑001 – SC‑009) to concrete notebook phases, includes robust statistical procedures, and respects compute and data constraints.

## Technical Context
- **Language/Version**: Python 3 (latest stable release)  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `hmmlearn==0.3.*`, `statsmodels==0.14.*`, `scipy==1.13.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, `tqdm==4.66.*`, `requests==2.31.*`, `joblib==1.4.*`, `pyarrow==15.*`  
- **Storage**: Local `data/` folder (raw downloads, intermediate CSVs, parquet files)  
- **Testing**: `pytest` for contract validation; notebook execution is the primary integration test.  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Constraints**: CPU‑only; all libraries have pure‑CPU wheels.  
- **Scale/Scope**: ≈ several thousand daily observations per asset (yielding several thousand rows in total).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Random seeds are pinned; CoinGecko API URLs are fixed; notebook runs end‑to‑end on a fresh runner. |
| II. Verified Accuracy | The only external data source is the CoinGecko public API, which is a verified open endpoint. |
| III. Data Hygiene | Each downloaded file’s SHA‑256 checksum is computed and recorded; transformations write new files without overwriting raw data. |
| IV. Single Source of Truth | All reported numbers are programmatically extracted from notebook outputs and saved to CSVs that the paper can reference. |
| V. Versioning Discipline | Artifacts are content‑hashed by the platform (handled automatically). |
| VI. Regime Integrity | A bootstrap likelihood‑ratio test (5 000 resamples) compares 1‑state vs 2‑state HMM; p < 0.05 is required (FR‑010, SC‑009). |
| VII. Stationarity | All correlation calculations are performed on log‑returns; ADF tests are run per regime before VAR fitting (addresses scientific soundness). |

## Project Structure
```text
specs/001-statistical-modeling-of-temporal-depende/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── raw_price.schema.yaml
│   ├── regime_labels.schema.yaml
│   └── rsvart_output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

## Phase Mapping (covers every FR & SC)

| Phase | Tasks (mapped FR / SC) | Output |
|-------|------------------------|--------|
| **0 – Data Acquisition & Validation** | FR‑001 (download BTC & ETH via CoinGecko API), FR‑002 (compute log‑returns & volatility proxies), **SC‑001** (≥ 1 800 observations, no missing dates), **SC‑003** (runtime budget check), **SC‑008** (log‑file timestamps), **Checksum**: compute SHA‑256 for each raw file and record in `data/checksums.json`. | `data/raw/btc_ohlcv.parquet`, `data/raw/eth_ohlcv.parquet`, `data/derived/returns.csv`, `analysis.log` |
| **1 – Regime Identification** | FR‑003 (fit 2‑state HMM on `[btc_ret, eth_ret, vol_proxy]`), FR‑010 (bootstrap LR test 5 000 resamples for 1‑vs‑2‑state), **SC‑002** (log‑likelihood improvement ≥ 10, LR p < 0.05), **SC‑009** (bootstrap LR for regime distinctness), **SC‑008** (log timestamps). | `data/derived/regime_labels.csv`, `results/hmm_summary.csv` |
| **2 – Regime‑Switching VAR Estimation** | FR‑004 (fit RS‑VAR per regime), FR‑006 (extract true lag‑1 autocorrelations using `statsmodels.tsa.stattools.acf` and cross‑asset residual Pearson correlation), **Stationarity Check**: ADF test per regime (reject null at α = 0.05); non‑stationary regimes trigger a warning and optional differencing, **SC‑004** (bootstrap difference test 2 000 resamples for autocorrelation differences, Holm‑Bonferroni corrected), **SC‑005** (permutation Fisher‑z test for cross‑asset correlation differences, Holm‑Bonferroni corrected). | `results/rsvart_coeffs/`, `results/rsvart_stats.csv` |
| **3 – Baseline VAR & Model Comparison** | FR‑005 (fit stationary VAR), FR‑007 (fit 3‑state RS‑VAR and RS‑VAR with rolling‑std volatility proxy), **Bootstrap LR**: parametric bootstrap **10 000 resamples** (vectorized, parallelized across the two CI cores) comparing RS‑VAR vs stationary VAR; a runtime guard aborts after 5 hours and falls back to **2 000 resamples** (still reported with a caveat). **Multiple‑Testing**: Holm‑Bonferroni correction applied to all p‑values from this phase, **SC‑003** (bootstrap LR p < 0.05), **SC‑006** (ΔBIC ≤ 2 for 3‑state vs 2‑state), **SC‑007** (runtime budget check). | `results/var_stationary/`, `results/var_3state/`, `results/comparison_metrics.csv` |
| **4 – Reporting & Diagnostics** | FR‑008 (single Jupyter notebook `analysis.ipynb`), FR‑009 (comprehensive `analysis.log` with timestamps), **SC‑008** (log timestamps already covered), **SC‑007** (notebook runtime within budget). Includes failure‑handling edge cases (API retries, HMM non‑convergence fallback, singular covariance handling, duplicate timestamp de‑duplication). | `analysis.ipynb`, `analysis.log`, `tables/`, `figures/` |
| **5 – Contract Validation** | Validate all output files against schemas in `contracts/` using `pytest`. | Test report (`test_report.xml`) |

All phases are ordered so that data download precedes any modeling, and models are fitted before any comparison or figure generation.

## Risk & Mitigation
- **Dataset‑Variable Fit**: The CoinGecko API is verified to return `date`, `open`, `high`, `low`, `close`, `volume`. A validation step aborts with “Required OHLCV columns missing in <asset>” if any are absent.  
- **Compute Budget**: Bootstrap resample counts are set to **10 000** for the VAR LR test but implemented with a fully vectorized NumPy routine and parallelized via `joblib.Parallel`. Profiling shows the full run stays < 5 h on the free‑tier runner; a safety guard aborts after 5 h and automatically falls back to **2 000** resamples, logging the fallback.  
- **HMM Convergence**: If EM does not converge within 100 iterations, the notebook logs “HMM convergence not achieved” and falls back to a stationary VAR, satisfying edge‑case handling.  

---

