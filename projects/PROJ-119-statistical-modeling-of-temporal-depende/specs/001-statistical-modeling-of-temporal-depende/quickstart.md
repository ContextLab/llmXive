# Quickstart: Running the Cryptocurrency Regime‑Switching Analysis

**Prerequisites**  
- GitHub Actions runner (or local Linux environment) with Python 3.11.  
- Internet access (to download the two open‑source datasets).  

**Step‑by‑Step**

1. **Clone the repository** (the project root).  
   ```bash
   git clone 
   cd PROJECT_REPO
   ```

2. **Create a virtual environment and install dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt   # pins all versions as listed in plan.md
   ```

3. **Run the notebook in a non‑interactive mode** (CI‑compatible)  
   ```bash
   papermill notebooks/analysis.ipynb output/analysis_executed.ipynb
   ```

   - The notebook will automatically download the BTC JSON and ETH parquet files from the verified URLs, verify required columns, and abort with a clear error if they are missing.  
   - All major steps are logged to `analysis.log`.  

4. **Inspect the outputs**  
   - Tables are written to `results/tables/`.  
   - Figures are written to `results/figures/`.  
   - The final regression summary is stored as `results/rsvart_summary.csv`.  

5. **Run contract validation (optional but recommended)**  
   ```bash
   pytest -q tests/contract/  # validates raw_price, regime_labels, rsvart_output schemas
   ```

6. **Check runtime compliance**  
   - The CI job prints `time -v` statistics; ensure `Maximum resident set size` ≤ 6 GB and total CPU time ≤ 2 h (typical for full bootstrap).  

**Re‑running with alternative settings**  
- To test the 3‑state model or the alternative volatility proxy, set the notebook parameters at the top of the file:
  ```python
  NUM_REGIMES = 3          # default 2
  VOL_PROXY = "rolling_std"   # options: "squared_returns", "rolling_std"
  ```
  Then repeat step 3.

**Troubleshooting**  
- *Missing required columns*: The notebook will stop with “Required OHLCV columns missing in <source>”. Verify that the dataset URLs have not changed.  
- *API failures*: The download block retries three times with exponential back‑off; persistent 5xx errors abort with “CoinGecko API unavailable”.  
- *HMM non‑convergence*: If EM does not converge within 100 iterations, the notebook falls back to a stationary VAR and logs “HMM convergence not achieved”.  

That’s all – the full analysis completes with a single command.

---
