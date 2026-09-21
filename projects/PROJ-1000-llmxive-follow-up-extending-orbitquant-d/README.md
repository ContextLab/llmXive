# llmXive: Automated Science Pipeline

A research implementation pipeline for data-agnostic quantization of diffusion transformers.

## Project Structure

```
llmxive/
├── code/ # Source code
│ ├── analysis/ # Analysis modules
│ ├── data/ # Data processing scripts
│ ├── models/ # Model wrappers and loaders
│ ├── quantization/ # Quantization engines
│ ├── validation/ # Validation scripts
│ └── config.py # Configuration management
├── data/ # Data storage
│ ├── processed/ # Processed datasets
│ └── figures/ # Generated visualizations
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
├── pyproject.toml # Project metadata and tool config
└── README.md # This file
```

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install development tools (optional):
 ```bash
 pip install -e ".[dev]"
 ```

## Usage

### Running the Pipeline

The main orchestration script is `code/main.py`:

```bash
python code/main.py
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Linting
ruff check code/ tests/

# Formatting
black code/ tests/
```

## Configuration

The project uses `code/config.py` for centralized configuration. You can also set environment variables:

- `LLMXIVE_DEVICE`: Device to use ("cpu", "cuda", or "auto")
- `LLMXIVE_SEED`: Random seed for reproducibility
- `LLMXIVE_BATCH_SIZE`: Batch size for data processing

## License

MIT License