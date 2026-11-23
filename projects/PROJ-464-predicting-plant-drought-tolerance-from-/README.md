# Predicting Plant Drought Tolerance from RSA Data

This repository implements a reproducible research pipeline that:

* Downloads publicly available root system architecture (RSA) images from the
 NPPN Plant Phenome Pipeline (via the verified MGB3 source).
* Extracts quantitative RSA metrics (depth, branching density, surface area)
 using CPU‑only OpenCV / scikit‑image processing.
* Retrieves physiological traits (e.g., stomatal conductance, photosynthetic
 rate) from the TRY database.
* Merges the datasets, performs collinearity checks, principal component
 analysis, and phylogenetic correction (PGLS).
* Fits regression and classification models, applies multiple‑comparison
 correction, and conducts sensitivity analysis.
* Generates a final markdown report with all figures, tables, and methodological
 notes.

The pipeline is orchestrated through `code/run_pipeline.py` and can be run
locally after installing the dependencies listed in `requirements.txt`.

## Quickstart

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-464-predicting-plant-drought-tolerance-from-

# Set up a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python code/run_pipeline.py
```

For detailed module‑level usage, see `specs/001-predicting-plant-drought-tolerance-from/quickstart.md`.
