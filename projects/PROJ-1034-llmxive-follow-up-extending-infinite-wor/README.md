# llmXive Follow-up: Extending Infinite Worlds with Versatile Interactions

Automated science pipeline for simulating and analyzing infinite worlds.

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Run Simulation
```bash
python -m code.cli.run_simulation --config path/to/config.yaml --steps 1000 --seed 42
```

### Generate Parameter Grid
```bash
python -m code.cli.generate_grid
```

### Run Sweep
```bash
python -m code.cli.run_sweep_execution
```

## Project Structure

```
.
├── code/
│ ├── cli/
│ ├── data/
│ ├── sim/
│ ├── analysis/
│ ├── tests/
│ ├── config.py
│ └── setup_project.py
├── data/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Format code:
```bash
black code/
ruff check code/
```