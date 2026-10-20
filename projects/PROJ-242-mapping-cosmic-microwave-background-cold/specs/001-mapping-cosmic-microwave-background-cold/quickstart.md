# Quickstart: Mapping CMB Cold Spots to Large‑Scale Structure

The quickstart guides a new researcher through a complete run of the analysis pipeline on the GitHub Actions free‑tier runner (CPU‑only).

## Prerequisites
* GitHub account with permission to run Actions on the repository.
* No local installation needed; everything runs in the CI environment.

## Steps

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-org/PROJ-242-mapping-cosmic-microwave-background-cold.git
   cd PROJ-242-mapping-cosmic-microwave-background-cold
   ```

2. **Inspect the workflow**  
   The workflow file is `.github/workflows/run_analysis.yml`. It sets up a Python 3.11 virtual environment, installs pinned dependencies from `requirements.txt`, and runs the full pipeline via `pytest -m contract`.

3. **Trigger the workflow**  
   ```bash
   git checkout -b quickstart-run
   git push origin quickstart-run
   ```
   Then go to the *Actions* tab on GitHub and click **Run workflow** (or rely on the push trigger).

4. **Monitor execution**  
   The job logs will display the major phases:
   * `Data Ingestion` – downloads the **Planck 2018 SMICA** CMB map and the **SDSS‑DR16** galaxy catalog, converts them to HEALPix nside = 64.
   * `Cold‑Spot Detection`
   * `Cross‑Correlation`
   * `Monte‑Carlo Simulations`
   * `Sensitivity Sweep`
   * `Memory‑Pressure Test (FR‑016)` – attempts to process a temporary `nside = 256` map and aborts with a clear log message if RAM would exceed 7 GB.
   Each phase prints progress counters and memory‑usage checkpoints. If memory exceeds 7 GB, the job aborts with the prescribed message (FR‑009).

5. **Retrieve results**  
   Upon successful completion, the workflow uploads the `results/` directory as an artifact. Download it from the *Artifacts* section. You will find:
   * `cold_spots.csv`
   * `xi_theta.npy`
   * `correlation_results.yaml`
   * `pvalue_table.csv`
   * PNG plots (`xi_theta.png`, `pvalue_heatmap.png`)
   * `analysis.ipynb` (full reproducible notebook)

6. **Inspect the notebook**  
   Open `analysis.ipynb` locally (or via GitHub's notebook viewer) to explore each step, re‑run cells, or modify parameters (e.g., change the detection threshold).

7. **Re‑run with custom parameters (optional)**  
   Edit `src/pipeline/config.yaml`:
   ```yaml
   detection:
     sigma_threshold: -2.0   # change to -2.5, etc.
     filter_radius_deg: 5    # change to 4, 6, …
   ```
   Commit and push; the CI workflow will re‑execute with the new settings.

## Expected Runtime & Resources
* **Wall‑clock time**: ≈ 4 h (worst‑case when all simulations run).  
* **Peak RAM**: ≤ 6.8 GB (verified on runner).  
* **Disk usage**: < 10 GB (all intermediate FITS files are compressed).

If the job exceeds the memory limit, it will abort with the logged message defined in FR‑009, and you can re‑run on a smaller sky fraction by adjusting `data.subset_fraction` in `config.yaml`.  
