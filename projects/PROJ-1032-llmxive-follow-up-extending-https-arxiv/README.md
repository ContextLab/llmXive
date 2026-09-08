# llmXive: Asynchronous RL Staleness Bounds for Low-Capacity Models

## Overview
This project investigates the impact of staleness in asynchronous reinforcement learning
on low-capacity models (Phi-2, Qwen1.5-1.8B) running on CPU.

## Project Structure
- `src/llmxive/`: Core library modules
- `src/cli/`: Command-line interface scripts
- `src/utils/`: Utility functions
- `tests/`: Test suite
- `data/`: Data storage (raw, processed, figures)

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`

## Usage
Run the trainer:
```bash
python -m src.llmxive.trainer
```

Generate baseline:
```bash
python -m src.llmxive.baseline_generator
```

## Testing
```bash
pytest
```

## Linting & Formatting
```bash
ruff check.
black.
```