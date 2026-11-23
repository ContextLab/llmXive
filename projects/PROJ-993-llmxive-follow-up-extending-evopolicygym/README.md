# PROJ-993: llmXive Follow-up: Extending EvoPolicyGym

This project implements the extension of the EvoPolicyGym framework to include:
1. **Dynamic Shift Environments**: Environments where reward/transition functions change at a configurable step.
2. **Counterfactual Explanation Generation**: CPU-tractable generation of natural language explanations for policy failures.
3. **Evolutionary Analysis Pipeline**: Statistical analysis of evolved policies using mixed-effects models.

## Project Structure

```
projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/
├── code/
│ ├── agents/ # Evolutionary harness and policy parsing
│ ├── analysis/ # Statistical analysis and metrics
│ ├── envs/ # Base and dynamic shift environments
│ ├── explanation/ # Counterfactual explanation generation
│ ├── tests/ # Unit and integration tests
│ ├── utils/ # Configuration, logging, seeding
│ └── main.py # CLI entry point
├── data/ # Generated datasets and logs
├── specs/ # Feature specifications and contracts
└── requirements.txt # Python dependencies
```

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the sensitivity analysis:
 ```bash
 python code/main.py --run-shift-sensitivity
 ```

3. Run the full evolution pipeline:
 ```bash
 python code/main.py --run-evolution
 ```

## Testing

Run tests using pytest:
```bash
pytest code/tests/
```
