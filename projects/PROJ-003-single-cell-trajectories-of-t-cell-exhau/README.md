# Single-Cell Trajectories of T-Cell Exhaustion

Automated pipeline for reconstructing T-cell exhaustion trajectories from scRNA-seq data.

## Prerequisites

- Python 3.9+
- R 4.3+ (with Seurat v4)
- SRA Toolkit

## Setup

1. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

2. Configure pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Development

### Linting & Formatting

Run linter:
```bash
make lint
```

Run formatter:
```bash
make format
```

Run both:
```bash
make check
```

### Testing

```bash
make test
```

## Project Structure

```
projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/
├── code/ # Pipeline scripts
├── data/ # Data directories (raw, processed, results)
├── tests/ # Test suite
├── config.yaml # Configuration file
├── pyproject.toml # Project metadata and tool configs
├── requirements.txt # Runtime dependencies
└── Makefile # Build automation
```

## Usage

See `quickstart.md` for detailed usage instructions.