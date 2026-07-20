# Quickstart Guide: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

This guide walks you through setting up the environment, downloading data, running the full analysis pipeline, and interpreting the results for the `PROJ-465` project.

## Prerequisites

- Python 3.9+
- `pip` (Python package manager)
- Access to the GWOSC API (no API key required for public events, but rate limits apply)

## 1. Installation

Clone the repository and install the required dependencies.

```bash
# Navigate to the project root
cd PROJ-465-quantifying-the-impact-of-data-resolutio

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

**Key Dependencies**:
- `gwpy`: For accessing GWOSC data.
- `bilby` & `dynesty`: For Bayesian parameter estimation.
- `scipy`, `numpy`, `pandas`: For data transformation and analysis.
- `matplotlib`: For visualization.

## 2. Configuration

Ensure the project directories exist. The `code/config.py` module handles this automatically upon first run, but you can verify:

```python
from code.config import ensure_directories
ensure_directories()
```

This creates the necessary structure:
- `data/raw/`: For downloaded strain data.
- `data/derived/`: For downsampled/quantized data.
- `results/posteriors/`: For Bayesian inference outputs.
- `results/metrics/`: For calculated bias and divergence metrics.

## 3. Data Download

The pipeline automatically fetches high-SNR (Signal-to-Noise Ratio ≥ 20) events from the GWOSC catalog.

To manually trigger a download for a specific event (e.g., GW150914):

```bash
python code/data/download.py --event GW150914
```

**Note**: The script includes logic to detect missing data segments. If data is unavailable for a requested segment, it logs a warning with the segment ID and proceeds with available data, as per the project's robustness requirements.

## 4. Running the Pipeline

The full analysis pipeline can be executed via the validation script, which orchestrates downloading, downsampling, inference, and metric calculation.

```bash
python code/validation/run_quickstart.py
```

This script performs the following steps:
1. **Ensures Event Data**: Fetches strain data for the target event.
2. **Runs Pipeline**:
 - **Downsampling**: Applies `scipy.signal.decimate` to generate 4096 Hz, 2048 Hz, and 1024 Hz versions.
 - **Quantization**: Simulates 16-bit and 32-bit float storage constraints.
 - **Inference**: Runs `bilby` with the `IMRPhenomPv2` waveform model and `dynesty` sampler (max 5000 steps, `dlogz` threshold 0.1).
 - **Metrics**: Calculates Hellinger distance and bias against the 4096 Hz baseline.
3. **Generates Checksums**: Verifies artifact integrity using `code/utils/hash_artifact.py`.
4. **Validates Artifacts**: Confirms that all expected output files (posteriors, metrics, reports) exist.

## 5. Output Artifacts

Upon successful completion, the following artifacts are generated:

- **Posteriors**: `results/posteriors/<event_id>_<resolution>.json`
 - Contains posterior samples and metadata, including "inconclusive" flags if convergence (`dlogz`) was not met.
- **Metrics**: `results/metrics/<event_id>_metrics.csv`
 - Contains Hellinger distance, mass/spin bias, and 90% CI comparisons.
- **Aggregation Report**: `results/metrics/aggregation_report.json`
 - Summarizes the majority-rule threshold where bias exceeds catalog uncertainty.
- **Visualizations**: `results/figures/sampling_rate_vs_bias.png`
 - Plots sampling rate against bias magnitude with the catalog uncertainty threshold line.

## 6. Interpreting Results

- **Inconclusive Runs**: If a posterior is flagged "inconclusive" (due to `dlogz > 0.1`), it is excluded from the denominator in the majority-rule calculation but counted as "bias exceeded" in the threshold analysis, per FR-004 and FR-007.
- **Bias Threshold**: The primary output is the lowest sampling rate where bias exceeds the catalog-reported 90% confidence interval for ≥ 50% of valid events.
- **No Threshold**: If bias remains within limits even at the lowest tested resolution (e.g., 1024 Hz), a "No threshold found" report is generated.

## Troubleshooting

- **Missing Data**: If the download fails due to missing segments, check the logs for the specific segment ID. The pipeline will continue with available data.
- **Convergence Failures**: If many runs are flagged "inconclusive", consider increasing the `dlogz` threshold or `max_steps` in `code/inference/run_bilby.py` (not recommended for standard runs).
- **API Rate Limits**: GWOSC may rate-limit requests. Add a small delay between downloads or use the `--wait` flag if available.

## Further Reading

- See `docs/data-model.md` for details on the data structures and artifact formats.
- Refer to `specs/001-quantify-gw-resolution-impact/spec.md` for the full requirements and user stories.
