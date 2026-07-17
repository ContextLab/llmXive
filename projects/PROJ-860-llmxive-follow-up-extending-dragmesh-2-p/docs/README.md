# llmXive: Virtual Tactile Zero-Shot Adaptation

## Project Overview

This project implements a virtual tactile sensing system for robotic manipulation
that adapts to unseen friction conditions using zero-shot learning techniques.
The system estimates friction coefficients in real-time and adjusts reward
scheduling accordingly to improve manipulation success rates.

## Key Features

- **Virtual Tactile Estimation**: Real-time friction coefficient estimation using
 torque and velocity ratios (FR-001)
- **Adaptive Reward Scheduling**: Dynamic adjustment of reward weights based on
 estimated friction (FR-002)
- **Novel Object Generation**: Procedural generation of randomized articulated
 geometries with varying friction properties (FR-003)
- **CPU-Only Execution**: Optimized for CPU-only environments with memory
 constraints (FR-004)

## User Stories

### US1: Zero-Shot Adaptation to Unseen Damping (P1 - MVP)
Implements the full adaptive policy loop that detects friction via $k_{est}$ and
adjusts rewards, verifying >15% improvement over static baseline on novel
high-friction objects.

### US2: Virtual Tactile Stiffness Estimation (P2)
Validates the $k_{est}$ estimator accuracy and stability under varying friction
and noise conditions.

### US3: CPU-Tractable Inference Pipeline (P3)
Ensures the entire experiment runs within 6 hours and 7GB RAM on a CPU-only runner.

## Architecture

```
code/
├── environment.py # PyBullet physics environment setup
├── estimator.py # VirtualTactileEstimator class
├── scheduler.py # AdaptiveRewardScheduler class
├── generator.py # NovelObjectSet generator
├── train.py # Training loop integration
├── evaluate.py # Evaluation and comparison
├── baseline_runner.py # Static baseline policy execution
├── aggregate.py # Log aggregation to CSV
├── analysis.py # Statistical analysis (t-tests)
├── seed_config.py # Reproducibility enforcement
├── logging_config.py # Logging setup
├── validation.py # Estimator validation suite
├── stress_test.py # Noise injection tests
├── memory_profiler.py # Memory profiling utilities
├── benchmark_runner.py # End-to-end benchmark execution
└── validate_citations.py # Citation verification

data/
├── raw/ # Raw experimental data
├── generated/ # Generated geometry files
└── results/ # Analysis results and metrics

tests/
├── unit/ # Unit tests
└── integration/ # Integration tests

state/ # Artifact hashes and tracking
docs/ # Documentation
```

## Requirements

- Python 3.8+
- CPU-only execution (no CUDA)
- Maximum 7GB RAM
- Maximum 6 hours wall-clock time

## Installation

```bash
cd code
pip install -r requirements.txt
```

## Quick Start

### 1. Generate Novel Objects
```bash
python generator.py --output../data/generated/ --count 30
```

### 2. Train Adaptive Policy
```bash
python train.py --objects../data/generated/ --epochs 100
```

### 3. Evaluate Both Policies
```bash
python evaluate.py --objects../data/generated/ --output../data/results/eval.csv
```

### 4. Aggregate Results
```bash
python aggregate.py --logs../data/results/ --output../data/results/aggregated.csv
```

### 5. Statistical Analysis
```bash
python analysis.py --input../data/results/aggregated.csv --output../data/results/analysis_report.json
```

### 6. Full Pipeline Benchmark
```bash
python benchmark_runner.py --output../data/results/benchmark.json
```

## Statistical Validation

The system uses paired t-tests to compare adaptive vs static policies:
- Null hypothesis: No difference in success rates
- Alternative hypothesis: Adaptive policy has >15% improvement
- Significance level: α = 0.05
- Power analysis ensures adequate sample size

## Reproducibility

All experiments use fixed seeds for reproducibility:
- Random seed: Set via `seed_config.py`
- NumPy seed: Set via `seed_config.py`
- PyBullet seed: Set via `seed_config.py`

Verify reproducibility by running:
```bash
python validate_citations.py
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with timeout
pytest tests/ --timeout=300

# Run specific test suite
pytest tests/unit/test_estimator.py -v
pytest tests/integration/test_pipeline.py -v
```

## Performance Constraints

- **Memory**: Peak usage ≤ 7GB (enforced via `memory_profiler.py`)
- **Time**: Wall-clock ≤ 6 hours (enforced via `pytest-timeout`)
- **Hardware**: CPU-only only (enforced via `environment.py`)

## Citation Verification

All external data sources and algorithms are verified via:
```bash
python validate_citations.py
```

This ensures:
- Requirements file citations match documentation
- Specification citations are accurate
- All data sources are properly attributed

## License

[License information to be added]

## Contributing

[Contribution guidelines to be added]
