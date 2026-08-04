# llmXive: Geometric Action Model for Robot Policy Learning

Automated science pipeline for extending geometric action models with symbolic planning.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── config.py # Configuration management
│ ├── data_generation.py # Synthetic data generation
│ ├── gfm_wrapper.py # GFM model wrapper
│ ├── inference_pipeline.py # Main inference orchestration
│ ├── symbolic_solver.py # Differentiable symbolic solver
│ ├── utils.py # Utility functions
│ └──...
├── data/
│ ├── raw/ # Raw input data
│ ├── generated/ # Generated datasets
│ └── results/ # Experiment results
├── tests/ # Test suite
├── scripts/ # Utility scripts
└── README.md
```

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # or
 venv\Scripts\activate # Windows
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Generating Test Set

```bash
python scripts/generate_test_set.py --seed 42 --trial-count 50
```

### Running Inference Pipeline

```bash
python code/inference_pipeline.py --config code/config.yaml
```

### Running Analysis

```bash
python code/analysis.py --symbolic data/results/symbolic_results.csv --baseline data/results/baseline_results.csv
```

## Configuration

Configuration is managed via `code/config.yaml`. Key parameters include:

- `topology_counts`: Range of hinge counts for kinematic chains
- `stiffness_range`: Stiffness values for deformable materials
- `trial_count`: Number of trials per experiment
- `sim_fps`: Simulation frames per second
- `target_zone`: Target location and radius for manipulation tasks

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## CI/CD

This project uses GitHub Actions for continuous integration. See `.github/workflows/ci.yml` for details.

## License

MIT License
