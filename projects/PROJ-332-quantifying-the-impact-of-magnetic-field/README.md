# Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Project ID**: PROJ-332
**Objective**: Automatically retrieve DIII-D discharge data, calculate magnetic topology metrics (island width, resonant surface density), and statistically correlate them with energy confinement time ($\tau_E$).

## 📖 Overview

This research pipeline investigates the hypothesis that specific magnetic field topological features (e.g., island width, density of rational surfaces) negatively impact plasma energy confinement time. The system automates the retrieval of experimental data from the public MDSplus archive, performs rigorous preprocessing, calculates derived metrics using physics-based equations (Rutherford equation), and conducts statistical analysis (Spearman rank correlation with bootstrap resampling) to validate the hypothesis.

### Key Features
- **Automated Data Retrieval**: Fetches EFIT, island, and confinement data for specified DIII-D discharge IDs from the MDSplus public archive.
- **Topology Metric Calculation**: Computes `island_width` and `resonant_surface_density` (count of rational surfaces $q=m/n$ per unit $\rho_{tor}$).
- **Statistical Rigor**: Includes power analysis, multicollinearity checks, and stratification by confinement mode (L-mode vs. H-mode).
- **Reproducibility**: All stochastic processes use fixed random seeds (`42`) and bootstrap iterations (`1000`).
- **Strict Validation**: Enforces schema contracts and minimum data thresholds (FR-001).

## 🏗️ Architecture

The project follows a modular, pipeline-based architecture:

```
PROJ-332
├── code/ # Source code
│ ├── data/ # Data retrieval, preprocessing, validation
│ ├── analysis/ # Metrics calculation, statistics, power analysis
│ ├── viz/ # Visualization (scatter plots)
│ ├── utils/ # Logging, limits, execution monitoring
│ └── main.py # Entry point
├── data/
│ ├── raw/ # Raw MDSplus data (if cached)
│ └── processed/ # Unified analysis CSVs
├── outputs/ # Final reports, plots, JSON summaries
├── contracts/ # JSON/YAML schemas for data validation
├── tests/ # Unit and integration tests
└── specs/ # Feature specifications and user stories
```

### Data Flow
1. **Retrieval (`code/data/retrieval.py`)**: Connects to MDSplus, fetches EFIT, `taue`, `h98y2`, and island data.
2. **Preprocessing (`code/data/preprocessing.py`)**: Parses time-series, aligns snapshots, determines confinement mode, and validates against `contracts/dataset.schema.yaml`.
3. **Metrics (`code/analysis/metrics.py`)**: Calculates `resonant_surface_density` and derives `island_width` via Rutherford equation if raw EFIT is available.
4. **Analysis (`code/analysis/correlation.py`)**: Performs power analysis, checks multicollinearity, stratifies by mode, and computes Spearman correlations with bootstrap CIs.
5. **Reporting (`code/analysis/report_generator.py`)**: Generates `summary_report.json` and diagnostic plots.

## 🚀 Quickstart

### Prerequisites
- Python 3.8+
- `mdsplus` libraries installed (system package or via `apt`/`yum` as per MDSplus documentation).
- Network access to `d3dds.ccr.ornl.gov` (MDSplus public archive).

### Installation
1. Clone the repository.
2. Install Python dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Ensure MDSplus is installed and `PATH`/`LD_LIBRARY_PATH` are configured.

### Execution
Run the pipeline with a list of DIII-D discharge IDs:
```bash
export DIII_D_DISCHARGES="123456,123457,123458"
python code/main.py
```
*Note: The pipeline will fail if fewer than 5 valid discharges are retrieved (FR-001).*

### Output Artifacts
- `data/processed/unified_analysis.csv`: Processed dataset with topology and confinement metrics.
- `outputs/summary_report.json`: Statistical results (correlation $r$, $p$-value, CI, power, hypothesis status).
- `outputs/topology_vs_confinement.png`: Scatter plot of island width vs. $\tau_E$.

## 📊 Statistical Methodology

- **Correlation**: Spearman rank correlation (non-parametric).
- **Significance**: Bootstrap resampling ($N=1000$, seed=42) for Confidence Intervals.
- **Power Analysis**: Calculated using `scipy.stats.zt_ind_solve_power` (Effect Size = 0.5, $\alpha$ = 0.05).
- **Stratification**: Separate correlations for L-mode and H-mode if $N \ge 3$ per group.
- **Multicollinearity**: Checked between $q_{range}$ and $resonant\_surface\_density$ (threshold = 0.95).

## 🛡️ Constraints & Compliance

- **Real Data Only**: No synthetic data fallbacks. If MDSplus fetch fails, the pipeline aborts.
- **Timeouts**: Per-operation timeout (default 300s) enforced via `code/utils/limits.py`.
- **Memory**: Target footprint < 7 GB; monitored via `code/utils/memory_monitor.py`.
- **Execution Time**: CI pipeline timeout set to 6 hours.

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```
Tests cover retrieval logic, schema validation, metric calculations, and statistical outputs.

## 📄 License
[Insert License Information Here]