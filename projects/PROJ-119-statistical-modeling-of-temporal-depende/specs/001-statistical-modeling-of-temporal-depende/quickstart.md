# Quickstart: Running the Cryptocurrency Regime‑Switching Analysis

**Prerequisites**  
- GitHub Actions runner (or a local Linux/macOS/Windows environment with Python 3.11).  
- Internet access (to download the data from the CoinGecko public API).  

**Step‑by‑Step**

1. **Clone the repository**  
   ```bash
   git clone <REPO_URL>
   cd <REPO_ROOT>
   ```

2. **Create a virtual environment and install exact dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the notebook in a non‑interactive, CI‑compatible mode**  
   ```bash
   papermill notebooks/analysis.ipynb output/analysis_executed.ipynb
   ```
   - The notebook automatically downloads the BTC and ETH OHLCV data **directly from the public CoinGecko API** for the most recent 5 years, validates required columns, and aborts with a clear error if validation fails.  
   - All major steps are logged to `analysis.log` (timestamps included).  

4. **Inspect the results**  
   - Tables are written to `results/tables/` (e.g., `regime_labels.csv`, `rsvart_stats.csv`).  
   - Figures are written to `results/figures/` (e.g., `acf_by_regime.png`).  
   - The final regression summary is stored as `results/rsvart_summary.csv`.  

5. **Run contract validation (optional but recommended)**  
   ```bash
   pytest -q tests/contract/
   ```
   This checks that `raw_price`, `regime_labels`, and `rsvart_output` files conform to the YAML schemas in `contracts/`.  

6. **Verify runtime compliance** (CI will automatically report). Locally you can run:
   ```bash
   /usr/bin/time -v papermill notebooks/analysis.ipynb output/analysis_executed.ipynb
   ```
   Ensure `Maximum resident set size` ≤ 6000 KB and total CPU time ≤ 2 h (typical for the full bootstrap).  

**Alternative Settings**  
- To test the 3‑state model or the rolling‑std volatility proxy, edit the top‑of‑notebook parameters:
  ```python
  NUM_REGIMES = 3          # default 2
  VOL_PROXY = "rolling_std"   # options: "squared_returns", "rolling_std"
  ```
  Then repeat step 3.

**Troubleshooting**  
- *Missing required columns*: Notebook aborts with “Required OHLCV columns missing in <asset>”. Verify that the CoinGecko API endpoints have not changed.  
- *Download failures*: The loader retries three times with exponential back‑off; persistent 5xx errors abort with “Data download unavailable”.  
- *HMM non‑convergence*: If EM does not converge within 100 iterations, the notebook logs “HMM convergence not achieved” and falls back to a stationary VAR.  
- *Bootstrap exceeds time limit*: The notebook automatically switches to a reduced 2 000‑sample bootstrap and records the fallback in `analysis.log`.  

That’s all – the full analysis completes with a single command.

---


