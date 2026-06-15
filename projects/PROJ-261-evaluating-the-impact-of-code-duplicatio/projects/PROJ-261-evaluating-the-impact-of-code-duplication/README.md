# PROJ-261: Evaluating the Impact of Code Duplication on LLM Code Understanding

## Overview

This project investigates the relationship between code duplication patterns and
language model perplexity, with the goal of understanding how syntactic clones
affect model comprehension and bug detection accuracy.

## Project Structure

```
projects/PROJ-261-evaluating-the-impact-of-code-duplication/
├── code/ # Python modules
│ ├── __init__.py
│ ├── config.py # Configuration parameters
│ ├── data_loader.py # Data downloading and streaming
│ ├── pii_scanner.py # PII detection
│ ├── ast_cloner.py # AST-based clone detection
│ ├── model_metrics.py # Perplexity computation
│ ├── bug_detection.py # HumanEval evaluation
│ ├── correlation_analysis.py
│ ├── visualization.py
│ ├── main.py # Pipeline orchestration
│ └── checksum_manifest.py # Artifact tracking
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed metrics
│ └── analysis/ # Analysis results and figures
├── tests/ # Test suites
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Contract tests
└── specs/001-evaluating-the-impact-of-code-duplication/
 ├── contracts/ # JSON/YAML schema definitions
 ├── research.md # Literature review
 ├── data-model.md # Entity definitions
 └── quickstart.md # Setup and usage guide
```

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the pipeline: `python code/main.py`

## License

Research project - see LICENSE for details.
