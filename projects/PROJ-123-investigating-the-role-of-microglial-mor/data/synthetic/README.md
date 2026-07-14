# Synthetic Microglia Dataset

This directory contains synthetically generated data for validating the
microglial morphology analysis pipeline.

**Contents:**
- `images/`: Synthetic microscopy images (PNG) of microglial cells.
- `microglia_metadata.json`: Metadata linking images to simulated cognitive
 scores, amyloid load, and brain regions.
- `microglia_ground_truth.csv`: The exact morphological metrics used to
 generate the images (branch points, soma area, etc.).

**Generation:**
These images are generated using `code/synthetic_data.py` via a simplified
reaction-diffusion inspired branching model. They are designed to mimic
the statistical properties of real microglia for pipeline testing purposes.

**Usage:**
Run the pipeline on this dataset to verify that the extracted metrics
in `data/processed/morphological_metrics.csv` match the ground truth
within the expected tolerance (e.g., 10% for branch points).
