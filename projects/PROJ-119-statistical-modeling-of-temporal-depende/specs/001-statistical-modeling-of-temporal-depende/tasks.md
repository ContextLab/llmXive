# Tasks: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

**Inputs**: `spec.md`, `plan.md`, reviewer feedback, existing contracts, and the research‑question validation.

The tasks below implement the full end‑to‑end pipeline, respect the data‑flow ordering, and address the statistical concern raised about the likelihood‑ratio test (Davies problem). Each task lists its primary output location and the verification step that will be used by the CI test suite.

---

- [ ] T001 [US-1] Download daily OHLCV data for Bitcoin and Ethereum (last 5 years) from the CoinGecko public API and store the raw files under `data/raw/`.   <!-- FAILED-IN-EXECUTION: code/download_raw_data.py exit=1 -->
  - **Path**: `data/raw/btc_ohlcv.parquet`, `data/raw/eth_ohlcv.parquet`  
  - **Verification**: Each file validates against `contracts/raw_price.schema.yaml`; compute SHA‑256 checksums and record them in `data/checksums.json`.  
  - **Reproducibility**: Set a fixed random seed (`np.random.seed(42)`) before any stochastic operation and log the seed value in `analysis.log`.  

- [ ] T002 [US-1] Compute daily log‑returns for BTC and ETH and create two volatility proxies (squared returns and 10‑day rolling standard deviation). Write the derived series to `data/derived/returns.csv`.  
  - **Path**: `data/derived/returns.csv`  
  - **Verification**: Schema‑validate the CSV against a generated `contracts/return_series.schema.yaml` (date, btc_return, eth_return, vol_sq, vol_10d_std). Ensure ≥ 1 800 rows and no missing dates (SC‑001).  
  - **Reproducibility**: Use the same fixed seed as T001 and record it in `analysis.log`.  

- [ ] T003 [US-1] Fit a 2‑state Hidden Markov Model on the joint vector `[btc_return, eth_return, vol_sq]` using `hmmlearn`. Output regime labels to `data/derived/regime_labels.csv` and perform a bootstrap likelihood‑ratio test (5 000 resamples) comparing the 1‑state vs 2‑state HMM.  
  - **Path**: `data/derived/regime_labels.csv`, `results/hmm/bootstrap_lr_1v2.json`  
  **Verification**:  
    – Regime label file validates against `contracts/regime_labels.schema.yaml`.  
    – Bootstrap LR p‑value < 0.05 must be recorded (SC‑002, SC‑009).  
    – Compute baseline 1‑state log‑likelihood; ensure 2‑state log‑likelihood improvement ≥ 10 points.  
    – Ensure EM convergence delta (change in log‑likelihood between iterations) < 1e‑4 and that fitting terminates within 100 iterations.  
    – Log convergence status, final log‑likelihood, improvement amount, and convergence delta in `analysis.log`.  

- [ ] T004 [US-3] Implement robust HMM failure handling: if EM does not converge within 100 iterations, log “HMM convergence not achieved”, fall back to a stationary VAR (see T006), and abort further regime‑specific steps.  
  - **Path**: `analysis.log` (error entry)  
  - **Verification**: CI checks that a non‑convergent run produces the fallback flag and does not attempt RS‑VAR fitting.  

- [ ] T005 [US-1] Fit a Regime‑Switching VAR (lag‑1) separately for each identified regime using `statsmodels.tsa.statespace.MarkovSwitching`. Export per‑regime model objects and summary statistics to `results/rsvart/` (e.g., `regime_1.json`, `regime_2.json`).  
  - **Path**: `results/rsvart/regime_1.json`, `results/rsvart/regime_2.json`, `results/rsvart/summary.csv`  
  - **Verification**:  
    – Each JSON conforms to `contracts/rsvart_output.schema.yaml`.  
    – Perform (a) a bootstrap Wald test (2 000 resamples) for differences in lag‑1 autocorrelation coefficients between regimes (SC‑004) and (b) a permutation‑based Fisher‑z test for cross‑asset residual correlation differences (SC‑005). Record p‑values in `summary.csv`.  

- [ ] T006 [US-2] Fit a stationary VAR (lag‑1) on the full return series. Compute BIC and run a parametric bootstrap likelihood‑ratio test (10 000 resamples) comparing the stationary VAR against the RS‑VAR fitted in T005. Store results under `results/comparison/`.  
  - **Path**: `results/comparison/stationary_var.json`, `results/comparison/bootstrap_lr_rsvart_vs_stationary.json`  
  - **Verification**:  
    – BIC value recorded.  
    – Bootstrap LR p‑value < 0.05 satisfies SC‑003 (using bootstrap rather than chi‑square to avoid the Davies problem).  

- [ ] T007 [US-2] Fit two alternative models for robustness: (a) a 3‑state RS‑VAR (using the same volatility proxy) and (b) a 2‑state RS‑VAR with the 10‑day rolling‑std volatility proxy. Compute BIC for each and report ΔBIC relative to the baseline 2‑state model.  
  - **Path**: `results/robustness/3state_rsvart.json`, `results/robustness/2state_rolling_std.json`, `results/robustness/bic_comparison.csv`  
  - **Verification**: ΔBIC ≤ 2 for the 3‑state model (SC‑006) and BIC values for the alternative proxy are recorded.  

- [ ] T008 [US-1] Assemble a single Jupyter notebook `analysis.ipynb` that orchestrates the entire pipeline: data download, preprocessing, HMM fitting, RS‑VAR estimation, baseline VAR, all bootstrap tests, robustness checks, and generation of tables/figures (regime‑specific autocorrelation tables, cross‑asset correlation heatmaps, BIC comparison plot). The notebook must run end‑to‑end on a fresh CI runner without manual intervention.  
  - **Path**: `analysis.ipynb`  
  - **Verification**: CI executes the notebook via `nbconvert --execute`; successful run produces all files listed above and exits with status 0 (SC‑007). Additionally, the notebook records its total wall‑clock execution time (using `time` or `%time`) in `analysis.log` and asserts that the runtime ≤ 2 hours (free‑tier limit).  

- [ ] T009 [US-3] Validate every output artifact against its JSON schema using a pytest suite located in `code/tests/`. The suite must be invoked in CI and produce a JUnit XML report `test_report.xml`.  
  - **Path**: `code/tests/test_schemas.py`, `test_report.xml`  
  - **Verification**: All schema checks pass (exit code 0).  

- [ ] T010 [US-3] Implement comprehensive error handling for the full pipeline:  
    1. Detect missing days in the OHLCV feed and abort with “Data gap detected: X consecutive missing days – aborting analysis.”  
    2. Retry CoinGecko API calls up to three times with exponential back‑off; abort with a clear error if all attempts fail.  
    3. De‑duplicate duplicate timestamps, keeping the first occurrence and logging the count removed.  
    4. Detect singular error‑covariance matrices during RS‑VAR fitting; drop the problematic regime, log the issue, and continue with remaining regimes.  
  - **Path**: `analysis.log` (all error messages) and relevant exception handling code in `code/pipeline.py`.  
  - **Verification**: Automated tests in `code/tests/test_error_handling.py` inject synthetic failures (e.g., NaNs, duplicate rows) and assert that the notebook aborts with the prescribed messages (SC‑008).  

--- 

*All tasks respect the ordering constraints and write only to project‑owned directories (`data/`, `results/`, `code/`, `analysis.ipynb`, `analysis.log`). The checklist provides a complete, reproducible research pipeline that satisfies every functional requirement, success criterion, and reviewer‑raised statistical concern.*  