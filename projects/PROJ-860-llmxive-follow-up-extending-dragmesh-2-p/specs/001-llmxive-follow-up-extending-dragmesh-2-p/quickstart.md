# Quickstart: Virtual Tactile Zero-Shot Adaptation

## Prerequisites

- Python 3.11+
- A Linux environment (GitHub Actions runner or local Linux/WSL2)
- 7GB+ RAM, 2+ CPU cores

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `pybullet`, `torch` (CPU), `numpy`, `pandas`, `pytest`, `scipy`, `statsmodels`, `psutil`.*

## Running the Experiments

### 1. Validate Citations and Manifest
Before running experiments, ensure data integrity and citation validity:
```bash
python code/utils/validate_citations.py
python code/utils/verify_manifest.py
```
*These scripts verify the DragMesh-2 manifest URL and compute the SHA256 checksum of the populated manifest file, storing it in the state YAML. A `citations_validation.log` file will be generated as evidence.*

### 2. Generate Novel Objects (Optional)
If you wish to inspect the generated object geometries:
```bash
python code/data/object_generator.py --count 5 --output data/generated/novel_objects/
```

### 3. Run the Full Sweep
Execute the main experiment (a sufficient number of trials, 50 objects, friction range 0.0–2.5, stratified):
```bash
python code/experiments/sweep_runner.py
```
*This script:*
- Downloads the DragMesh-2 manifest if missing.
- Generates a set of novel objects, comprising both high-friction and full-range variants.
- Runs the static and adaptive policies on each object.
- Logs results to `data/generated/sweep.csv`.
- Monitors system resources.
- **Estimated Time**: ~4-5 hours on a 2-core CPU.

### 4. Analyze Results
Run the statistical analysis:
```bash
python code/experiments/stats_analyzer.py
```
*This generates `data/results/stat_test_results.json` containing the GLMM results, Odds Ratios, and pass/fail status for SC-001 and SC-002.*

## Verifying the Output

1. **Check the logs**: Ensure `data/generated/sweep.csv` contains a sufficient number of rows to support the experimental design (multiple objects across trials and policies).
2. **Check the stats**: Open `data/results/stat_test_results.json` and verify:
   - `high_friction_subset.odds_ratio` > 1.0 and `p_value` < 0.05 (SC-001).
   - `full_range_varying.odds_ratio` > 1.0 and `p_value` < 0.05 (SC-002).
3. **Check the system metrics**: Open `data/results/system_metrics.json` and verify:
   - `total_wall_clock_hours` <= 6.0 (SC-003).
   - `peak_ram_gb` <= 7.0 (SC-004).
4. **Check the manifest hash**: Verify `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` contains the correct `artifact_hashes.data_raw`.

## Troubleshooting

- **OOM Error**: If you encounter Out of Memory errors, reduce the `--trials` argument in `sweep_runner.py` (e.g., to 50) and note the power limitation in the final report.
- **CUDA Error**: If you see CUDA-related errors, ensure `torch` is installed in CPU-only mode (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) and that no GPU devices are detected.
- **Manifest Download Failure**: Verify internet connectivity. The manifest is small (<10MB) and should download instantly.
- **Zero Success Baseline**: If the static policy fails [deferred] of trials in a subset, the GLMM will still compute an Odds Ratio; do not panic if the "improvement %" calculation would otherwise be undefined.