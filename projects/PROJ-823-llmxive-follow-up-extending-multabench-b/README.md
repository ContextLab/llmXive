# llmXive Follow-up: Extending MulTaBench

This project extends MulTaBench with CPU-tractable baseline generation and tabular-conditioned projection modules.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Install development dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

## Project Structure

- `code/`: Source code
- `tests/`: Test suite
- `data/`: Data artifacts (input and output)
- `figures/`: Generated plots and visualizations
- `specs/`: Design documents and specifications

## Usage

See individual pipeline scripts in `code/pipelines/` for usage instructions.

## License

MIT