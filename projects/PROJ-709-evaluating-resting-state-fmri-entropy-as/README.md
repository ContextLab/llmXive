# Evaluating Resting-State fMRI Entropy as a Biomarker for Attention-Deficit Traits

## Project Structure
```
.
├── code/ # Source code
├── data/
│ ├── raw/ # Raw dataset downloads
│ ├── processed/ # Preprocessed data
│ └── derived/ # Derived datasets and results
├── tests/ # Test suites
├── docs/ # Documentation
└── specs/ # Project specifications
```

## Quickstart
```bash
# Setup virtual environment
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt

# Run data loader
python code/data_loader.py
```

## Configuration
- Dataset: OpenNeuro ds000305 (ADHD-200)
- Parameters: m=2, r=0.2*SD, FD threshold=0.2, target volumes=120

## License
MIT License