# Quickstart: Reconstructing Solar Irradiance from Historical Sunspot Records

## Prerequisites

- Python 3.11 or higher
- Git
- Access to GitHub Actions (for CI/CD) or a local environment

## Installation

1. **Clone the Repository**:
 ```bash
 git clone https://github.com/your-org/your-repo.git
 cd your-repo
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Data Download

The pipeline requires several external datasets that must be obtained manually from primary canonical sources.

| Dataset | Manual Download URL | Destination |
|---------|--------------------|-------------|
| GSN (Group Sunspot Number) | <https://www.sidc.be/silso/datafiles> (Download `gsn_monthly.csv`) | `data/raw/gsn_monthly.csv` |
| SORCE/TIM TSI | <https://lasp.colorado.edu/home/sorce/data/> (Download `TIM_v5.csv`) | `data/raw/sorce_tim.csv` |
| CMIP6 v3.2 Solar Forcing | <> (Filter: `variable: rsdt`, `experiment: historical`) | `data/raw/cmip6_tsi.parquet` |
| 14C Cosmogenic Isotope | <https://www.ncei.noaa.gov/access/paleo-search/> (Search for "IntCal20" or "Δ14C") | `data/raw/14c_delta.csv` |
| 10Be Cosmogenic Isotope | <https://www.ncei.noaa.gov/access/paleo-search/> (Search for "10Be") | `data/raw/10be_concentration.csv` |
| Mg II Index (optional) | <> | `data/raw/mgii_index.csv` |

After placing each file in the indicated location, run the checksum verification script:

```bash
python code/data/download.py --verify
```

The script will compute SHA‑256 hashes and record them in `state/projects/PROJ-381-reconstructing-solar-irradiance-from-his.yaml`.

## Preprocessing

Run the preprocessing script to clean and engineer features:

```bash
python code/data/preprocess.py
```

This script will:
- Interpolate missing GSN values linearly.
- Apply the Hilbert‑Huang Transform (via `pyhht`) to detect solar cycle boundaries and compute a **cycle_phase** feature (fractional position within each cycle).
- Split the satellite‑era data into training (early period) and validation (later period) sets.
- One‑hot encode `cycle_phase` into a discrete set of bins and normalize numeric columns.
- Save processed Parquet files to `data/processed/`.

## Model Training

Train the cycle‑specific regression model:

```bash
python code/models/train.py
```

This script will:
- Perform k‑fold cross‑validation on the training set.
- Conduct **Leave-One-Cycle-Out CV** (LOCO-CV) across solar cycles within the training period.
- Tune Random Forest hyper‑parameters (`n_estimators≤100`, `max_depth≤10`).
- Optionally train a sparse Gaussian Process if `--gp` flag is set.
- Save the trained model to `code/models/`.

## Reconstruction

Apply the trained model to pre‑satellite GSN data:

```bash
python code/models/reconstruct.py
```
- Generates a continuous TSI reconstruction for the early modern period through 2002.
- Propagates cross‑validation error and isotope-adjusted uncertainty to produce lower/upper uncertainty bands.
- Saves `reconstruction.parquet` to `data/results/`.

## Baseline Comparison

Compare the new reconstruction against the 2007 baseline and CMIP6:

```bash
python code/models/evaluate.py
```

This script:
- Loads the **fixed** 2007 baseline (Lean et al.) as an external reference (no re-tuning).
- Computes RMSE reduction percentage, R², and correlation with CMIP6.
- Saves metrics to `data/results/metrics.json`.

## Statistical Significance Testing

Perform **proxy‑augmented** block‑bootstrap resampling:

```bash
python code/analysis/bootstrap.py
```

This script:
- Executes 1 000 block‑bootstrap iterations on reconstruction variance **and** on isotope proxy variance.
- Applies Bonferroni correction for the three minima comparisons.
- Outputs `bootstrap_stats.json` with corrected p‑values and confidence intervals.

## Visualization

Generate plots for variance confidence intervals, difference plots, and baseline comparison:

```bash
python code/analysis/plots.py --variance-ci
python code/analysis/plots.py --baseline-comparison
```

## Troubleshooting

- **Missing Data**: Ensure all files are placed in `data/raw/` with the exact filenames listed above.
- **HHT Errors**: If `pyhht` fails, verify that the input data is clean and has no NaNs after interpolation.
- **Memory Errors**: Reduce the `n_estimators` parameter in `config.py` if memory limits are exceeded.