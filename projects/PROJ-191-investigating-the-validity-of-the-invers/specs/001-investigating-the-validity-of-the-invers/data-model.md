# Data Model: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Entity Definitions

### 1. RawDataFile
Represents a downloaded file from arXiv.
-   `file_path`: string (relative to `data/raw/`)
-   `source_url`: string (verified arXiv URL)
-   `checksum_sha256`: string
-   `format`: string (e.g., "csv", "ascii", "tar")
-   `extracted_files`: list of strings (paths to extracted contents)

### 2. HarmonizedDataset
The unified dataset used for inference.
-   `separation_m`: array(float) - Aligned separation distances in meters.
-   `force_n`: array(float) - Force values in Newtons.
-   `uncertainty_stat`: array(float) - Statistical uncertainty (1$\sigma$) in Newtons.
-   `uncertainty_sys`: array(float) - Systematic uncertainty (1$\sigma$) in Newtons.
-   `covariance_matrix`: string (path to `.npz` or `.memmap` file) - Full $N \times N$ covariance matrix stored on disk.
    -   Diagonal: $(\text{uncertainty\_stat})^2 + (\text{uncertainty\_sys})^2$
    -   Off-diagonal: 0.0 (due to lack of correlation data).
-   `source_runs`: list of strings - IDs of original experimental runs included.
-   `interpolation_method`: string (e.g., "linear", "cubic")
-   `storage_type`: string ("memmap" if N > 80000, "numpy" otherwise)

### 3. InferenceResult
Output of the MCMC/Nested Sampling run.
-   `model_name`: string ("Newtonian" or "Yukawa")
-   `samples`: array(float, 2D) - Posterior samples (walkers $\times$ steps $\times$ params).
-   `params`: list of strings - ["alpha", "lambda", "scale", "sys_scale"]
-   `log_evidence`: float - $\ln Z$ from `dynesty`.
-   `gelman_rubin`: float - Convergence statistic.
-   `credible_interval_95`: dict - {"alpha": [low, high], "lambda": [low, high], "sys_scale": [low, high]}

### 4. RobustnessReport
Output of LOO and Injection-Recovery tests.
-   `loo_iterations`: list of InferenceResult - Results for each excluded run.
-   `injection_recovery`: dict - {"injected_alpha": float, "recovered_alpha": float, "recovered_interval": [low, high], "success": bool}
-   `null_simulation`: dict - {"bayes_factor_mean": float, "false_positive_rate": float}
-   `stability_metric`: float - Variation in upper limits across LOO iterations (must be < 15%).

## Data Flow

1.  **Ingestion**: `RawDataFile` -> `harmonize.py` -> `HarmonizedDataset`.
2.  **Inference**: `HarmonizedDataset` + `config.yaml` -> `mcmc.py`/`nested.py` -> `InferenceResult`.
3.  **Validation**: `HarmonizedDataset` + `InferenceResult` -> `robustness.py` -> `RobustnessReport`.

## Storage Format

-   **HarmonizedDataset**: Saved as `data/harmonized/dataset_v1.csv` (for tabular data) and `data/harmonized/covariance_v1.npz` (for the matrix, or `.memmap` for large N).
-   **InferenceResult**: Saved as `results/inference_run_001.json` (summary) and `results/samples_run_001.h5` (large samples).
-   **RobustnessReport**: Saved as `results/robustness_report.json`.