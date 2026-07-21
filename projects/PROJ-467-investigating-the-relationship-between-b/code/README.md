# llmXive: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination

## Project Overview
This project investigates the relationship between brain network dynamics (derived from fMRI data) and individual differences in tactile discrimination abilities.

## Quick Start
```bash
# Setup environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run preprocessing
python -m src.brainnet.preprocessing --input data/raw/ --output data/processed/

# Run analysis
python -m src.brainnet.analysis --max-subjects 100
```

## Structure
- `src/brainnet/`: Main source code
- `data/raw/`: Raw input data
- `data/processed/`: Preprocessed data
- `results/`: Analysis results
- `tests/`: Unit and integration tests

## License
MIT
