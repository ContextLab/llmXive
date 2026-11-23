# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python **3.11**
- `git`, at least 1 GB free disk space, internet access for installing packages.

## Installation
```bash
git clone <repo-url>
cd autocorr-mobius
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Demo
The project provides a lightweight demonstration that runs the full pipeline on a tiny subset of the data. This verifies the installation and the end-to-end logic in seconds.

Execute the demo command:
```bash
python -m code.main --demo
```

### Expected Demo Artefacts
The demo command produces the following files:
- `data/mobius_array.npy` – A small Möbius sequence ($N=2000$) stored as an `int8` NumPy array.
- `data/window_starts.json` – A JSON file containing one window start index for each interval length.
- `data/processed/demo_autocorr.csv` – A CSV containing the normalized autocorrelation for the first sampled window ($L=1000, h=1$).
- `figures/heatmap_demo.png` – A PNG heat-map visualizing the demo result.

You can verify their existence with:
```bash
ls data/mobius_array.npy data/window_starts.json data/processed/demo_autocorr.csv figures/heatmap_demo.png
```

## Running the Full Pipeline
To process the full dataset ($N=10^7$, all windows, 1,000 permutations per window, and visualizations), omit the `--demo` flag:

```bash
python -m code.main
```

### Full Pipeline Outputs
| Path | Description |
|------|-------------|
| `data/raw/mobius_2bit.npy` | 2-bit packed deterministic Möbius sequence (FR-001). |
| `data/raw/mobius_array.npy` | `int8` working copy of the Möbius sequence. |
| `data/processed/window_index.csv` | The sampled window start indices. |
| `data/processed/autocorrelation_stats.csv` | All statistical results (p-values, CIs). |
| `data/processed/sensitivity_summary.csv` | Zero-density sensitivity analysis results. |
| `data/processed/calibration_test.json` | SC-005 null calibration results. |
| `data/processed/empirical_uniformity.json` | Empirical uniformity check on real data. |
| `data/processed/pipeline_status.json` | Per-stage status log. |
| `outputs/figures/heatmap_L{L}.png` | Heat-maps for $L \in \{10^3, 10^4, 10^5\}$. |

## Project Layout
- `code/`: Python modules for the sieve, autocorrelation, permutations, and visualization.
- `data/raw/`: Immutable raw data artifacts.
- `data/processed/`: Intermediate and final statistical results.
- `outputs/figures/`: Final research figures.
- `tests/`: Unit and integration tests.
- `contracts/`: Data schemas for validation.
