# llmXive: Self-Improving Language Models with Bidirectional Evolutionary Search

This project implements a hybrid evolutionary search framework where a small LLM performs the forward step (trajectory recombination) and a symbolic planner performs the backward step (sub-goal decomposition).

## Prerequisites

- Python 3.11+
- Git
- CUDA is **NOT** supported; this project runs entirely on CPU.

## Setup

1. **Clone and Setup Environment**
 ```bash
 git clone <repository-url>
 cd projects/PROJ-884-llmxive-follow-up-extending-self-improvi

 # Create virtual environment
 python3.11 -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate

 # Install dependencies
 pip install -r requirements.txt
 ```

2. **Initialize Project Structure**
 ```bash
 python code/setup_structure.py
 python code/setup_data_dirs.py
 ```

3. **Generate Initial Dataset**
 ```bash
 python code/dataset/generate_dataset.py
 # Output: data/raw/puzzles.json (with checksums in data/raw/.checksums.json)
 ```

## Running the BES Loop

The main experiment orchestrates the Bidirectional Evolutionary Search (BES) loop, alternating between the LLM forward step and the symbolic backward step.

```bash
python code/main.py --config config/default.yaml
```

### Configuration

Edit `config/default.yaml` to adjust:
- `population_size`: Number of individuals in the evolutionary population
- `generations`: Number of evolutionary iterations
- `model_id`: Hugging Face model ID for the forward step (default: `distilbert-base-uncased`)
- `max_time_seconds`: Wall-clock time limit for the experiment

### Expected Output

After execution, the following artifacts are generated in `data/processed/`:
- `experiment.log`: JSON log with timestamps, wall-clock time, and resource usage
- `metrics.csv`: Success rates, execution times, and complexity analysis
- `scaling_analysis.csv`: Log-log regression results for complexity class derivation
- `final_report.md`: Comprehensive report with statistical significance tests

## Interpreting Results

### Success Rate Comparison

The `final_report.md` contains a section comparing the success rates of the symbolic-guided BES versus the neural-verifier baseline. Success rate is defined as the proportion of puzzles solved within the time budget.

### Statistical Significance

- **Z-Test**: A two-tailed two-proportion z-test (FR-005) determines if the difference in success rates is statistically significant (alpha=0.05).
- **TOST**: Equivalence testing (SC-001) checks if the symbolic approach is statistically equivalent to the baseline within a predefined margin.

### Complexity Analysis

The `scaling_analysis.csv` file contains the derived Big-O complexity class (e.g., O(n), O(n^2)) based on log-log linear regression of problem size vs. execution time.

### Cost Comparison

Energy consumption (Joules) and wall-clock time are logged for each method. Lower values indicate better efficiency.

## Project Structure

```
projects/PROJ-884-llmxive-follow-up-extending-self-improvi/
├── code/
│ ├── dataset/ # Puzzle generation and verification
│ ├── symbolic/ # Formal parser and symbolic planner
│ ├── bes/ # Evolutionary search components
│ ├── analysis/ # Metrics, statistics, and report generation
│ ├── utils/ # Logging, seeding, and configuration
│ ├── config.py # Configuration management
│ ├── exceptions.py # Custom exception classes
│ └── main.py # Main experiment orchestrator
├── data/
│ ├── raw/ # Immutable puzzle dataset (JSON + checksums)
│ └── processed/ # Logs, metrics, and final reports
├── tests/
│ ├── unit/ # Unit tests for individual components
│ └── integration/ # Integration tests for the BES loop
├── config/ # Experiment configuration files
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Validation

To ensure data integrity, run the checksum validation script:
```bash
python code/dataset/validate_checksums.py
```

To run the full test suite:
```bash
pytest tests/
```

## License

This project is part of the llmXive research initiative. See the LICENSE file for details.