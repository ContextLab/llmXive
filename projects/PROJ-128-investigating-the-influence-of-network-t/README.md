# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Project Overview
This research project analyzes the relationship between structural brain connectivity (derived from diffusion MRI) and spontaneous functional activity patterns (derived from fMRI). We compute topological graph metrics (global efficiency, clustering, modularity) and dynamic functional state metrics (dwell time, state transitions) to investigate their statistical associations.

**Important**: All findings are framed as **associational**. We do not claim causal prediction.

## Key Features
- **Structural Analysis**: Computes graph metrics from dMRI tractography.
- **Dynamic Functional Analysis**: Implements a strict **Leave-One-Out (LOO) K-Means** clustering approach (k=5) to derive recurrent activity states, ensuring no circular correlation between subjects.
- **Statistical Rigor**: Normality testing (Shapiro-Wilk), Pearson/Spearman correlation selection, and Benjamini-Hochberg FDR correction.
- **Robustness**: Sensitivity analysis on window length (30 TR vs 20 TR) and density thresholds.
- **CPU-Only**: Optimized for CPU execution with memory constraints.

## Architecture
The pipeline is modular:
- `code/preprocess/`: Data loading, sliding window correlation, LOO clustering.
- `code/analysis/`: Correlation testing, FDR correction, robustness checks.
- `code/reports/`: Report generation and language auditing.

See `docs/ARCHITECTURE.md` for detailed structure.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline
```bash
python code/main.py
```

### 3. Validate Outputs
```bash
python code/validate_quickstart.py
```

## Data
This project uses **HCP (Human Connectome Project)** data fetched from OpenNeuro.
- **dMRI**: Structural connectivity matrices.
- **fMRI**: Resting-state time series.

*Note: Real data fetching is required. Synthetic data is not supported.*

## Results
The pipeline produces:
- `data/processed/structural_metrics.csv`
- `data/processed/dynamic_metrics.csv`
- `data/processed/correlation_results.csv`
- `data/reports/final_report.json`

## Constraints
- **No GPU**: Designed for CPU-only environments.
- **No Synthetic Data**: All metrics must derive from real HCP data.
- **Associational Framing**: Reports explicitly avoid causal language.

## License
Research use only.

## Contact
For questions regarding the methodology or implementation, refer to the `docs/` directory.