# llmXive: Quantifying the Impact of Codebase Age on LLM Code Understanding

## Project Overview

This project investigates the correlation between the age of codebase artifacts (measured by median commit age) and the performance of Large Language Models (LLMs) in code understanding tasks. We analyze whether older code is harder for LLMs to understand, as measured by perplexity and functional correctness rates.

## Research Questions

1. Is there a significant correlation between codebase age and LLM code understanding metrics?
2. Can quantized small-scale CodeLLMs perform effectively on CPU hardware?
3. How do complexity and token length act as covariates in this relationship?

## Project Structure

```
.
├── code/
│ ├── extraction/ # Git history analysis and snippet extraction
│ ├── inference/ # Model loading, inference, and metrics calculation
│ ├── analysis/ # Statistical correlation and reporting
│ ├── models.py # Data models and entities
│ ├── utils/ # Logging, configuration, hashing utilities
│ └── setup_*.py # Project initialization scripts
├── data/
│ ├── raw/ # Raw repository clones
│ ├── extracted/ # Extracted snippets CSV
│ ├── aggregated/ # File-level aggregated metrics
│ ├── results/ # Final correlation results and reports
│ └── models/ # Cached model weights
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── specs/ # Research design documents
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- Git (for repository cloning and history analysis)
- At least 8GB RAM (for CPU-only inference)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive-quantifying-age-impact
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Set up linting and formatting:
 ```bash
 python code/setup_linting.py
 ```

## Quick Start

For detailed step-by-step instructions, see `specs/001-quantify-age-impact/quickstart.md`.

### Phase 1: Data Extraction

Extract function-level Python snippets from target repositories:

```bash
python code/extraction/run_extraction.py \
 --repos "" \
 --output data/extracted/snippets.csv
```

### Phase 2: Inference

Run CPU-only inference on extracted snippets:

```bash
python code/inference/run_inference.py \
 --input data/extracted/snippets.csv \
 --output data/aggregated/file_metrics.csv \
 --timeout 300
```

### Phase 3: Analysis

Perform statistical correlation analysis:

```bash
python code/analysis/correlation.py \
 --input data/aggregated/file_metrics.csv \
 --output data/results/correlation_results.csv
```

Generate the final report:

```bash
python code/analysis/report_generator.py \
 --input data/results/correlation_results.csv \
 --output data/results/final_report.md
```

## Data Models

The project uses the following core data entities (defined in `code/models.py`):

- `Snippet`: Represents a function-level code snippet with metadata
- `Repository`: Represents a source code repository
- `InferenceResult`: Stores LLM inference metrics for a snippet
- `FileMetric`: Aggregated metrics at the file level

## Research Design

See `specs/001-quantify-age-impact/` for:
- Experimental design and methodology
- User stories and acceptance criteria
- Data model specifications
- Research contracts and constraints

## Testing

Run unit tests:
```bash
python -m pytest tests/unit/ -v
```

Verify extraction output:
```bash
python code/extraction/verify_extraction.py --input data/extracted/snippets.csv
```

Verify inference output:
```bash
python code/inference/verify_inference_output.py --input data/aggregated/file_metrics.csv
```

Verify final report:
```bash
python code/analysis/verify_report.py --input data/results/final_report.md
```

## Configuration

Core configuration is managed in `code/utils/config.py`:
- Random seeds for reproducibility
- Timeout limits (default: 1-hour per task)
- Directory paths

## Logging

Unified logging is configured via `code/utils/logging.py`. Set the `LOG_LEVEL` environment variable to adjust verbosity (DEBUG, INFO, WARNING, ERROR).

## License

This research project is provided for academic and research purposes.

## Contributing

When implementing new tasks:
1. Follow the existing API surface in sibling files
2. Use real data sources only (no fabricated data)
3. Write complete, executable code (no stubs or TODOs)
4. Ensure all scripts produce real output files to disk
5. Run tests to verify correctness
