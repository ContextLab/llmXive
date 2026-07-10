# The Influence of Visual Complexity on Implicit Bias

Automated research pipeline for quantifying visual complexity and analyzing its impact on implicit bias scores (D-scores) using Permutation Tests.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis (Permutation, PCA, Power)
│ ├── data/ # Data loading, processing, and aggregation
│ ├── stimuli/ # Image complexity metrics (Edge, Entropy, Fractal)
│ ├── utils/ # Logging and utilities
│ ├── viz/ # Visualization (Plots)
│ ├── config.py # Configuration and path management
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/
│ │ ├── stimuli/ # Input background images
│ │ └── responses/ # Raw IAT response logs
│ ├── processed/ # Intermediate data (complexity scores, D-scores)
│ └── results/ # Final analysis outputs (JSON, plots)
├── tests/ # Test suite
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## Prerequisites

- Python 3.11+
- System dependencies for OpenCV (e.g., `libgl1`, `libglib2.0-0` on Linux)

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
cd code
pip install -r requirements.txt
```

## Usage

### Running the Full Pipeline

Execute the main script to run the entire analysis pipeline:

```bash
cd code
python main.py
```

This will:
1. Load and validate stimuli images.
2. Compute visual complexity metrics (Edge Density, Entropy, Fractal Dimension).
3. Process raw IAT response logs into D-scores.
4. Run Permutation Tests with LOIO sensitivity analysis.
5. Generate publication-quality plots and save results to `data/results/`.

### Command Line Arguments

```bash
python main.py [--null-effect] [--seed SEED]
```

- `--null-effect`: Run in synthetic mode for CI/testing (generates dummy data).
- `--seed`: Set random seed for reproducibility (default: 42).

### Running Specific Modules

**Stimuli Processing:**
```bash
python -m stimuli.process
```

**Data Aggregation:**
```bash
python -m data.process
```

**Statistical Analysis:**
```bash
python -m analysis.permutation
```

## Output Artifacts

Upon successful completion, the following files are generated:

- `data/processed/complexity_scores.csv`: Visual complexity metrics per image.
- `data/processed/aggregated_d_scores.csv`: Participant D-scores per session.
- `data/results/permutation_results.json`: Statistical test results (p-value, effect size).
- `data/results/sensitivity_results.json`: LOIO and threshold sensitivity data.
- `data/results/power_analysis.json`: Post-hoc power calculation.
- `figures/`: Publication-quality plots (Boxplots, Sensitivity curves).

## Testing

Run the test suite using pytest:

```bash
cd code
pytest tests/ -v
```

## Methodology Note

This project employs a **Permutation Test** (rather than ANOVA) to assess the influence of visual complexity on implicit bias. This methodological choice, documented in `docs/research.md`, is designed to handle stimulus-set confounds and provide robust p-value estimation without strict parametric assumptions.

## License

[Insert License Here]
