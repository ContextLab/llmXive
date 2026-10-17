# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python 3.11+, `git`, ≥ 1 GB free disk, internet for package install.

## Installation
```bash
git clone 
cd autocorr-mobius
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
python code/main.py
```
Stages (fault-isolated; a non-core failure is logged to `data/processed/pipeline_status.json` without aborting):

| Stage | Description | Output |
|-------|-------------|--------|
| Sieve + 2-bit packing | μ(n), 1 ≤ n ≤ 10⁷, packed ternary array (FR-001) | `data/raw/mobius_2bit.npy`, `data/raw/mobius_array.npy` |
| Windows | multiple non-overlapping windows per L (seed 20231017) | `data/processed/window_index.csv` |
| Autocorrelation | FFT, all lags ≤ L/2, with exact int64 cross-validation | partial `autocorrelation_stats.csv` |
| Permutation null | 1,000 zero-preserving sign shuffles per window | p-values, CIs in CSV |
| FDR correction | Benjamini–Hochberg, α = 0.05 | `adjusted_p_value` column |
| Null calibration (SC-005) | Chi-square + subsample KS on simulated random-sign windows | `calibration_test.json` |
| Empirical uniformity | Same tests on real μ p-values (labeled research result) | `empirical_uniformity.json` |
| Sensitivity | ±5 %/±10 % zero-density, batched FFT, raw p < 0.05 criterion (FR-007) | `sensitivity_summary.csv` |
| Visualization | Heatmaps with zero contour + CI bands | `outputs/figures/heatmap_L*.png` |

### Expected Outputs
| Path | Description |
|------|---------|
| `data/raw/mobius_2bit.npy` | 2-bit packed deterministic Möbius sequence (FR-001). |
| `data/raw/mobius_array.npy` | int8 working copy (exact unpack of the packed array). |
| `data/processed/window_index.csv` | The sampled windows. |
| `data/processed/autocorrelation_stats.csv` | All statistics (schema: `contracts/mobius_stats.schema.yaml`). |
| `data/processed/sensitivity_summary.csv` | Zero-density sensitivity results (raw + FDR status per affected lag). |
| `data/processed/calibration_test.json` | SC-005 null calibration (simulated random-sign windows). |
| `data/processed/empirical_uniformity.json` | Empirical uniformity on real data (labeled result). |
| `data/processed/pipeline_status.json` | Per-stage status log (incl. int64 cross-check, sensitivity scope). |
| `outputs/figures/heatmap_L{1000,10000,100000}.png` | Heatmaps (≥ 1200 × 1200 px). |

## Running Individual Stages
```bash
python code/sieve.py --output data/raw/mobius_array.npy --packed data/raw/mobius_2bit.npy
python code/autocorrelation.py --array data/raw/mobius_array.npy --out data/processed/autocorrelation_stats.csv
python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy
python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json
python code/sensitivity.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy --out data/processed/sensitivity_summary.csv
python code/viz.py --stats data/processed/autocorrelation_stats.csv --outdir outputs/figures/
```

## Verification Steps
1. Möbius arrays: `np.unique(arr)` yields the expected distinct sign values; shape `(10000000,)`; packed array shape `(5000000,)`, dtype `uint8`; pack/unpack round-trip exact.
2. `pytest tests/unit/ -v` (includes viz zero-contour, calibration, 2-bit round-trip, and sensitivity runtime regression tests).
3. `pytest tests/integration/test_pipeline.py -v` (reduced N = 10⁶; injects a stage failure and asserts graceful continuation).
4. Inspect a CSV row:
   ```python
   import pandas as pd
   df = pd.read_csv('data/processed/autocorrelation_stats.csv')
   print(df[(df.interval_length==1000) & (df.lag==1)].head())
   ```
5. Heatmap resolution:
   ```python
   from PIL import Image
   img = Image.open('outputs/figures/heatmap_L10000.png')
   print(img.size, img.format)  # ≥ (1200, 1200), PNG
   ```

## Troubleshooting
- **Sensitivity timeout (T012)**: the stage is batched and checkpointed; if it still exceeds 4 h it applies the documented degradation to L ∈ {10³, 10⁴}, logged in `pipeline_status.json` (full scope remains the deliverable when runtime permits).
- **Zero line placement (T014)**: the zero line is a contour at color-value 0 overlaid on the heatmap (`plt.contour(..., levels=[0.0])`), not an `axhline`; the CI band lives on a twin panel sharing the lag axis.
- **Pipeline abort (T017)**: `main.py` isolates stage failures; check `pipeline_status.json` for the failing stage and re-run that stage's individual command.
- **p-value of 0.0**: impossible by the +1 correction (minimum 1/1001); NaN autocorrelation rows correspond to all-zero windows flagged `not_applicable`.
- **Calibration vs. empirical uniformity**: `calibration_test.json` validates the test on simulated random-sign windows (SC-005); `empirical_uniformity.json` reports the real-data result — a rejection there is a finding about μ, not a broken test.

## Reproducibility Checklist
- [x] Fixed seed 20231017 everywhere (per-window seeds derived deterministically).
- [x] Dependencies pinned in `requirements.txt`.
- [x] Checksums recorded for all data artifacts (both raw arrays).
- [x] Re-running `main.py` on a fresh runner yields byte-identical CSV and PNGs (verified by checksum in the integration test).

## Expected Runtime (GitHub Actions free tier)
Sieve + packing ~2 s; autocorrelation + cross-validation [deferred]; permutation null ~2–3 h; calibration [deferred]; sensitivity ~1.5 h (documented degradation guard); FDR < 1 min; visualization [deferred]; total ~4–5 h < 6 h limit.