# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Project Overview

This project investigates whether topological properties of structural brain networks derived from diffusion MRI (dMRI) predict the prevalence, stability, and switching speed of recurrent activity patterns observed in resting-state functional MRI (fMRI).

The analysis pipeline computes:
- **Structural Graph Metrics**: Global efficiency, average clustering coefficient, and modularity from dMRI-derived connectivity matrices.
- **Dynamic Functional Metrics**: Dwell time and number of visited states from fMRI data using a Leave-One-Out (LOO) k-means clustering approach.
- **Structure-Function Correlations**: Statistical correlations between structural and dynamic metrics, corrected for multiple comparisons using the Benjamini-Hochberg procedure.
- **Robustness Analysis**: Sensitivity checks on window length (30 TR vs 20 TR) and structural threshold density.

## Research Question

> Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns?

## Data Source

This pipeline uses the **HCP 1200 Subjects Release** from the Human Connectome Project, accessed via the OpenNeuro repository (ds000031).

- **dMRI**: Diffusion-weighted images for structural connectivity.
- **fMRI**: Resting-state fMRI data for dynamic functional connectivity.

## Prerequisites

- Python 3.9+
- CPU-only execution (no GPU required)
- Sufficient RAM (~7 GB) and disk space (~14 GB) for processing

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

The `code/config.py` file contains all configurable parameters:
- **Sliding Window**: 30 TR baseline, 1 TR step (sensitivity check: 20 TR).
- **Clustering**: k=5 states, Leave-One-Out (LOO) strategy.
- **Statistical Thresholds**: α=0.05 for normality, q=0.05 for FDR correction.
- **Graph Sparsity**: Exclude subjects with sparsity > 90%.

## Pipeline Execution

Run the full pipeline:
```bash
python code/main.py
```

This will:
1. Download HCP data (if not already present).
2. Preprocess dMRI/fMRI data.
3. Compute structural and dynamic metrics.
4. Perform correlation analysis.
5. Generate robustness reports.
6. Output final results to `data/processed/`.

## Output Artifacts

| File | Description |
|------|-------------|
| `data/processed/structural_metrics.csv` | Graph metrics per subject (efficiency, clustering, modularity). |
| `data/processed/dynamic_metrics.csv` | Dynamic metrics per subject (dwell time, visited states). |
| `data/processed/correlation_results.csv` | Correlation matrix (r, p, FDR-corrected p). |
| `data/logs/exclusion_log.json` | Log of excluded subjects and reasons. |
| `data/processed/sensitivity_results.json` | Robustness analysis results (window length, density). |
| `data/reports/final_report.json` | Comprehensive report with "associational" framing. |

## Key Methodological Constraints

- **LOO Clustering**: To prevent circular correlation, centroids are derived from all subjects *except* the target subject.
- **Associational Framing**: All reports explicitly state that findings are correlational, not causal.
- **CPU-Only**: No GPU acceleration; designed for limited compute environments.
- **Real Data Only**: No synthetic or placeholder data is used. The pipeline fails loudly if real HCP data cannot be fetched.

## Robustness Checks

- **Window Length**: Compares 30 TR baseline against 20 TR sensitivity check.
- **Density Threshold**: Varies structural threshold by ±5%.
- **Resource Monitoring**: Tracks peak RAM and runtime to ensure compliance with CPU constraints.

 ## License

This project is for research purposes only. Data usage must comply with HCP data use agreements.