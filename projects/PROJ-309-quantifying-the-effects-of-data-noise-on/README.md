# Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

## Setup

### Prerequisites
- Python 3.9+
- pip

### Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

### Linting and Formatting
This project uses **Ruff** for linting and **Black** for formatting.

**Format code:**
```bash
black code/ tests/
```

**Lint code:**
```bash
ruff check code/ tests/
```

**Run both:**
```bash
black code/ tests/ && ruff check code/ tests/
```

## Usage
Run the full pipeline:
```bash
python code/main.py
```

Or using the entry point:
```bash
run-pipeline
```

## Project Structure
```
├── code/ # Source code
├── data/
│ ├── raw/ # Clean trajectories
│ ├── processed/ # Noisy trajectories & metrics
│ └── results/ # Final outputs & figures
├── tests/
│ ├── unit/
│ ├── contract/
│ └── integration/
├── requirements.txt
├── pyproject.toml # Project metadata, Black, and Ruff config
└── README.md
```