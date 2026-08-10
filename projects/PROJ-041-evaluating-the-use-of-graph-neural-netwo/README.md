# LLMXive GNN Anomaly Detection Project

## Setup Linting and Formatting

This project uses `ruff` for linting and `black` for formatting.

### Installation

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install ruff black pre-commit
 ```

2. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

### Usage

- **Lint**: Run `ruff check.`
- **Format**: Run `black.`
- **Check before commit**: `pre-commit run --all-files`

## Configuration

- **Black**: Configured in `pyproject.toml` (line-length: 88)
- **Ruff**: Configured in `pyproject.toml` (select: E4, E7, E9, F, I, N, W)
- **Pre-commit**: Configured in `.pre-commit-config.yaml`