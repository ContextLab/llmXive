# PROJ-860: llmXive Follow-up - Extending DragMesh-2-P

## Virtual Tactile Zero-Shot Adaptation

This project implements a virtual tactile sensing system for robotic manipulation
that adapts to unseen friction conditions using zero-shot learning techniques.

## Quick Links

- [Full Documentation](docs/README.md)
- [API Reference](docs/API.md)
- [User Stories](docs/US1.md, docs/US2.md, docs/US3.md)

## Installation

```bash
# Install dependencies
pip install -r code/requirements.txt

# Run tests
pytest code/tests/ -v
```

## Usage

### Generate Training Objects
```bash
python code/generator.py --output data/generated/ --count 30
```

### Train Adaptive Policy
```bash
python code/train.py --objects data/generated/ --epochs 100
```

### Evaluate and Compare
```bash
python code/evaluate.py --objects data/generated/ --output data/results/eval.csv
```

### Analyze Results
```bash
python code/aggregate.py --logs data/results/ --output data/results/aggregated.csv
python code/analysis.py --input data/results/aggregated.csv
```

## Key Features

- **Real-time Friction Estimation**: Virtual tactile sensing via torque/velocity ratios
- **Adaptive Reward Scheduling**: Dynamic reward adjustment based on estimated friction
- **Novel Object Generation**: Procedural generation of randomized geometries
- **CPU-Optimized**: Runs within 7GB RAM and 6 hours on CPU-only hardware

## Validation

- **Statistical Significance**: Paired t-tests with p < 0.05
- **Performance Threshold**: >15% improvement over static baseline
- **Reproducibility**: Fixed seeds across all random operations
- **Data Integrity**: SHA-256 checksums for all data artifacts

## Project Structure

```
.
├── code/ # Source code
│ ├── environment.py # Physics simulation
│ ├── estimator.py # Tactile estimation
│ ├── scheduler.py # Reward scheduling
│ ├── generator.py # Object generation
│ ├── train.py # Training loop
│ ├── evaluate.py # Evaluation
│ ├── aggregate.py # Log aggregation
│ ├── analysis.py # Statistical analysis
│ └──... # Additional modules
├── data/ # Data artifacts
│ ├── raw/ # Raw data
│ ├── generated/ # Generated geometries
│ └── results/ # Analysis results
├── tests/ # Test suite
├── docs/ # Documentation
├── state/ # Artifact tracking
├── requirements.txt # Dependencies
└── README.md # This file
```

## Contributing

Please read the [contributing guidelines](CONTRIBUTING.md) before submitting
pull requests.

## License

[License to be specified]
