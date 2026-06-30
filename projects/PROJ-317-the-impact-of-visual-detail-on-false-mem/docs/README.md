# Visual Detail and False Memory Susceptibility Research Pipeline

**Project ID**: PROJ-317
**Status**: Active Research Pipeline

## Overview

This project implements an automated pipeline to investigate the impact of visual detail on false memory susceptibility. The system generates manipulated stimuli, simulates participant sessions, and performs statistical analysis on the resulting data.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis and visualization
│ ├── data/ # Data loading, processing, and ethics
│ ├── participants/ # Participant simulation interface
│ ├── stimuli/ # Image manipulation pipeline
│ ├── utils/ # Utility functions (logging, config)
│ ├── cli.py # Command-line interface
│ ├── config.py # Configuration management
│ └── requirements.txt # Python dependencies
├── data/ # Data storage
│ ├── stimuli/ # Original and manipulated images
│ ├── stimuli_metadata/ # YAML metadata for stimuli
│ ├── responses/ # Participant response data
│ ├── processed/ # Intermediate and final analysis data
│ ├── ethics/ # Ethics documentation
│ └── logs/ # System logs
├── docs/ # Documentation
│ ├── README.md # This file
│ └── ethics/ # Ethics guidelines (linked from data/)
└── tests/ # Test suites
 ├── unit/ # Unit tests
 ├── integration/ # Integration tests
 └── contract/ # Contract tests
```

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
cd code
pip install -r requirements.txt
```

## Quick Start

### 1. Setup Project Structure

Ensure all required directories exist:

```bash
python setup_project_structure.py
```

### 2. Generate Mock Stimuli

Run the image manipulation pipeline to create enhanced and reduced detail images:

```bash
python cli.py manipulate --input data/stimuli/raw --output data/stimuli/manipulated
```

This generates:
- `data/stimuli/manipulated/`: Manipulated images
- `data/stimuli_metadata/`: YAML metadata files for each image

### 3. Run Power Analysis

Calculate the required sample size before data collection:

```bash
python cli.py power-analysis
```

Output: `data/processed/power_analysis.json`

### 4. Simulate Participant Sessions

Run simulated participant sessions to generate response data:

```bash
python cli.py simulate --n-sessions 10 --output data/responses
```

### 5. Statistical Analysis

Perform repeated-measures ANOVA and generate visualizations:

```bash
python cli.py analyze --input data/responses --output data/processed
```

Outputs:
- `data/processed/anova_results.json`: Statistical test results
- `data/processed/bonferroni_results.json`: Corrected p-values
- `figures/false_memory_rates.png`: Visualization with confidence intervals

## Configuration

Configuration is managed via `code/config.py`. Default paths are relative to the project root.

Key configuration options:
- `ALPHA_LEVEL`: Significance level for statistical tests (default: 0.05)
- `POWER_TARGET`: Target statistical power (default: 0.80)
- `EFFECT_SIZE`: Expected effect size (Cohen's f, default: 0.25)
- `DATASET_SOURCE`: Source for images (default: 'mock')

## Ethics

This research involves simulated participants. All data is synthetic. For real human subjects research, IRB approval is required.

- **Informed Consent Template**: `data/ethics/informed_consent.md`
- **IRB Placeholder**: `data/ethics/irb_placeholder.md`
- **GDPR Compliance**: See `data/ethics/` for data handling guidelines.

## Testing

Run the test suite:

```bash
pytest tests/
```

### Test Coverage

- **Unit Tests**: `tests/unit/` - Tests for individual functions and classes
- **Integration Tests**: `tests/integration/` - Tests for full pipeline workflows
- **Contract Tests**: `tests/contract/` - Tests for API compliance

## Logging

Logs are stored in `data/logs/`:
- `system.log`: General system logs
- `manipulation_errors.log`: Errors during image manipulation
- `session_errors.log`: Errors during participant simulation

To view logs:

```bash
tail -f data/logs/system.log
```

## Troubleshooting

### Image Manipulation Fails

Check `data/logs/manipulation_errors.log` for specific errors. Ensure input images are valid PNG/JPG files.

### Missing Dependencies

Re-run `pip install -r requirements.txt` to ensure all packages are installed.

### Data Directory Not Found

Run `python setup_project_structure.py` to create the required directory structure.

## Contributing

1. Create a feature branch.
2. Implement changes following the existing code style (black, ruff).
3. Add or update tests as needed.
4. Submit a pull request.

## License

This project is for research purposes only.

## Contact

For questions, refer to the project documentation or the `docs/ethics/` directory for compliance guidelines.
