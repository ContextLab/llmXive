# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python **3.11** or newer
- `git`, at least 1 GB free disk space, internet access for installing packages.

## Installation
```bash
git clone <repo-url>
cd autocorr-mobius
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Demo
The project provides a lightweight demo that runs the full pipeline on a tiny subset of the data (so it finishes in seconds). Execute it with:

```bash
python -m code.main --demo
```

The demo creates the following artefacts:

- `data/mobius_array.npy` – a small Möbius sequence (N = 2000) stored as an `int8` NumPy array.
- `data/window_starts.json` – a JSON file containing one window start index for each interval length.
- `data/processed/demo_autocorr.csv` – a CSV with a single autocorrelation value for the first window (L = 1000, h = 1).
- `figures/heatmap_demo.png` – a PNG heat‑map visualising the demo autocorrelation.

You can verify their existence with:

```bash
ls data/mobius_array.npy data/window_starts.json data/processed/demo_autocorr.csv figures/heatmap_demo.png
```

## Running the Full Pipeline
To process the full data set (N = 10⁷, all windows, permutations, visualisations, etc.) omit the `--demo` flag:

```bash
python -m code.main
```

## Verification
- The quickstart file contains the string `--demo`. [UNRESOLVED-CLAIM: c_28322aaa — status=not_enough_info]
- Running the demo command exits with status 0 and produces the files listed above. [UNRESOLVED-CLAIM: c_635bb2cc — status=not_enough_info]