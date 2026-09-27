# llmXive: Predicting Plant Drought Tolerance from RSA Data

This project implements an automated scientific pipeline to predict plant drought tolerance using Root System Architecture (RSA) metrics derived from root images and physiological trait data.

## Overview

The pipeline follows a strict workflow:
1. **Data Acquisition**: Fetches root images from NPPN and physiological traits from TRY.
2. **Preprocessing**: Extracts RSA metrics (depth, branching density, surface area) using OpenCV and scikit-image.
3. **Integration**: Merges data with phylogenetic structures for robust statistical analysis.
4. **Modeling**: Fits OLS, Ridge, Lasso, Random Forest, and Phylogenetic Generalized Least Squares (PGLS) models.
5. **Validation**: Performs sensitivity analysis and VIF compliance checks to ensure robust, non-circular claims.

## Project Structure

```text
.
├── code/ # Implementation modules
│ ├── analysis.py # Statistical analysis & sensitivity
│ ├── config.py # Configuration & hyperparameters
│ ├── download_images.py# NPPN image fetching
│ ├── download_traits.py# TRY trait fetching
│ ├── fetch_phylogeny.py# Phylogenetic tree fetching
│ ├── generate_report.py# Final report generation
│ ├── merge_data.py # Data merging logic
│ ├── models.py # Model definitions & fitting
│ ├── preprocess_images.py # RSA metric extraction
│ └──... (other utilities)
├── data/
│ ├── raw/ # Raw downloaded data (images, traits)
│ └── derived/ # Processed data (CSVs, trees)
├── docs/ # Documentation
├── results/ # Final reports and figures
├── state/ # Intermediate state files (VIF checks, proxies)
├── contracts/ # JSON schemas for data validation
└── tests/ # Unit and integration tests
```

## Quick Start

See [`docs/quickstart.md`](quickstart.md) for installation and execution instructions.

## API Reference

See [`docs/api_reference.md`](api_reference.md) for detailed module documentation.

## Requirements

* Python 3.11+
* Dependencies listed in `requirements.txt` (pandas, numpy, scikit-learn, scipy, statsmodels, opencv-python, scikit-image, caper, huggingface_hub, etc.)

## Data Sources

* **NPPN Plant Phenome Pipeline**: Root images (via HuggingFace).
* **TRY Database**: Physiological traits (stomatal conductance, photosynthesis).
* **Open Tree of Life**: Phylogenetic trees.

## License

[Insert License Information]
