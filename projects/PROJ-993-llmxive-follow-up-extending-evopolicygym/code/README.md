# EvoPolicyGym Extension Project

This project extends the EvoPolicyGym framework to include dynamic shift environments,
counterfactual explanation generation, and evolutionary harness analysis.

## Structure

- `agents/`: Evolutionary agents and harnesses
- `analysis/`: Statistical analysis pipelines
- `envs/`: Gymnasium environments including dynamic shift variants
- `explanation/`: Counterfactual explanation generation and validation
- `tests/`: Unit and integration tests
- `utils/`: Configuration, logging, and seed management utilities

## Usage

```bash
# Run shift sensitivity analysis
python main.py --run-shift-analysis

# Run full evolution pipeline
python main.py --run-evolution
```
