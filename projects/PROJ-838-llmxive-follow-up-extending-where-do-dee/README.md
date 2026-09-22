# llmXive Follow-up: Extending "Where Do Deep-Research Agents Go Wrong?"

This project implements a pipeline to analyze the topological properties of early trajectory spans in deep-research agents, predicting collapse based on connectivity and branching metrics.

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration
│ ├── downloader.py # Dataset fetching
│ ├── graph_builder.py # Graph construction
│ ├── metrics.py # Metric calculation
│ ├── evaluator.py # Evaluation and prediction
│ └── pipeline.py # Main orchestration
├── data/
│ ├── raw/ # Raw dataset
│ └── processed/ # Processed artifacts
├── tests/ # Test suite
├── requirements.txt # Dependencies
└── README.md # This file
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the full pipeline:

```bash
python code/pipeline.py --config code/config.py
```

See `quickstart.md` for detailed instructions.

## Key Features

- **Graph Construction**: Parses trajectories and builds DAGs based on co-reference/citation logic
- **Metric Calculation**: Computes global connectivity and average branching factor
- **Prediction**: Uses a 20th percentile threshold (per Spec FR-004) to predict collapse
- **Evaluation**: Provides precision, recall, F1, and correlation analysis
- **Robustness**: Includes sensitivity analysis and power analysis

## Output

The pipeline generates comprehensive reports in `data/processed/` including:
- Metrics CSV
- Threshold configurations
- Evaluation results
- Sensitivity matrices
- Power analysis

## Dependencies

- pandas
- networkx
- scikit-learn
- spaCy
- tqdm
- pyyaml
- requests
- scipy
- numpy
- datasets
- matplotlib

## License

[Insert License]
