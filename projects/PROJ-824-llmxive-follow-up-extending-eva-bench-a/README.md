# PROJ-824: llmXive Follow-up - Extending EVA-Bench

This project implements a latency injection framework to evaluate voice agent robustness against network delays, extending the EVA-Bench dataset.

## Prerequisites

- Python 3.11+
- CPU-only execution (No GPU/Quantization)

## Installation

```bash
pip install -r requirements.txt
```

## Project Structure

- `code/`: Source code modules
 - `data/`: Dataset downloading and checksum management
 - `processing/`: Latency injection and pipeline execution
 - `analysis/`: Statistical modeling and regression
 - `tests/`: Unit and integration tests
- `data/`: Downloaded datasets and generated artifacts
- `results/`: Analysis outputs and reports
- `config.py`: Global configuration settings
