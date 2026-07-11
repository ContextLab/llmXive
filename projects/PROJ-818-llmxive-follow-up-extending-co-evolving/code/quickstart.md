# Quickstart

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
pip install -e.
```

## Basic Usage

1. **Generate Configuration**:
 ```python
 from src.utils.config import Config
 cfg = Config(seed=42, generation_count=10, rule_evaluation_budget=1000)
 cfg.to_file("config.json")
 ```

2. **Run Pipeline** (once components are implemented):
 ```bash
 python -m src.cli --config config.json
 ```

## Structure

- `src/`: Source code
- `tests/`: Test suite
- `data/`: Generated datasets and results
- `specs/`: Feature specifications