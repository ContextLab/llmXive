# Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

**Project ID**: PROJ-800-assessing-parcellation-sensitivity-of-hu
**Branch**: main
**Status**: Active Development

## Description

This project investigates the sensitivity of brain network hub identification to the choice of parcellation atlas (AAL-90, Schaefer-200, Schaefer-400) using healthy adult fMRI data.

The pipeline performs the following steps:
1. **Data Acquisition**: Downloads raw fMRI NIfTI files from OpenNeuro/HCP datasets.
2. **Parcellation**: Generates adjacency matrices for three distinct atlas resolutions.
3. **Centrality Analysis**: Computes Degree and Betweenness centrality metrics.
4. **Hub Definition**: Identifies hub nodes based on a proportional threshold (default 10%).
5. **Sensitivity Quantification**: Calculates Excess Overlap indices, Spearman correlations, and performs Spatial Spin Tests to evaluate the stability of hub definitions across resolutions.

## Requirements

See `requirements.txt` for the full list of dependencies (e.g., `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `pytest`).

## Usage

```bash
# Setup environment
pip install -r requirements.txt

# Run the full pipeline
python code/main.py --subjects 20 --atlas all
```

## Project Structure

- `data/raw`: Raw fMRI data and atlas masks.
- `data/processed`: Generated adjacency matrices and spatial mappings.
- `data/results`: Centrality scores, overlap statistics, and visualizations.
- `code`: Implementation modules for data processing, analysis, and visualization.
- `tests`: Unit and integration tests for TDD compliance.

## License

Research Use Only.