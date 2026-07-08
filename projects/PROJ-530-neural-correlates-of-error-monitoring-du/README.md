# PROJ-530: Neural Correlates of Error Monitoring During Simulated Navigation

This project analyzes the relationship between MFN (Medial Frontal Negativity) amplitude and error magnitude during simulated navigation tasks.

## Setup

1. Create the project directory structure:
 ```bash
 python -c "from code.setup_directories import create_project_directories; create_project_directories()"
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Preprocessing
```bash
python code/preprocess.py
```

### Analysis
```bash
python code/analysis.py
```

### Visualization
```bash
python code/viz.py
```

## Project Structure

```
projects/PROJ-530-neural-correlates-of-error-monitoring-du/
├── data/
│ ├── raw/ # Raw data files
│ └── processed/ # Preprocessed data
├── results/
│ ├── models/ # Saved models
│ ├── figures/ # Generated plots
│ └── diagnostics/ # Diagnostic reports
├── code/ # Source code
└── tests/ # Test suite
```

## Dependencies

See `requirements.txt` for the full list of dependencies.

## License

MIT License