# llmXive: Infinite Worlds with Versatile Interactions

Automated science pipeline for simulating and analyzing complex systems.

## Project Structure

- `src/`: Source code
 - `sim/`: Simulation engines (Eco-Director, Baselines)
 - `analysis/`: Statistical analysis tools (LMM, RF, ACF)
 - `data/`: Data loading and processing
 - `cli/`: Command-line interfaces
 - `tests/`: Test utilities
- `data/`: Input and output data
- `tests/`: Test suite

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m src.cli.run_simulation --steps 1000
```

## Testing

```bash
pytest tests/
```