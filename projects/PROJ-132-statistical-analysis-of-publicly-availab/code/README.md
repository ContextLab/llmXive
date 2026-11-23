# Bird Migration and Climate Change Analysis

Statistical analysis of publicly available bird migration patterns and climate change correlations.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd bird-migration-analysis
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

### Running the Pipeline

```bash
python code/run_pipeline.py
```

### Data Preparation

The pipeline expects data in the `data/raw/` directory. To download or generate synthetic data:

```bash
python code/src/data/download.py
```

### Preprocessing

Run the preprocessing pipeline:

```bash
python code/src/data/preprocess.py
```

### Modeling

Run the GAMM modeling pipeline:

```bash
python code/src/models/gamm_fit.py
```

## Testing

Run all tests:

```bash
pytest tests/
```

Run specific test suites:

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/
│ │ │ ├── download.py
│ │ │ ├── preprocess.py
│ │ │ └── impute.py
│ │ ├── models/
│ │ │ ├── gamm_fit.py
│ │ │ ├── utils.py
│ │ │ └── trajectory.py
│ │ └── lib/
│ │ ├── config.py
│ │ └── logging_config.py
│ ├── tests/
│ │ ├── unit/
│ │ ├── integration/
│ │ └── contract/
│ ├── run_pipeline.py
│ └── setup_project.py
├── data/
│ ├── raw/
│ ├── interim/
│ └── processed/
├── logs/
├── state/
└── docs/
```

## Configuration

Environment variables can be used to configure the pipeline:

- `SEED`: Random seed for reproducibility (default: 42)
- `GRID_RES`: Grid resolution in degrees (default: 0.5)
- `SAMPLE_SIZE`: Target sample size for tail-preserving sampling (default: None)
- `PERMUTATIONS`: Number of permutations for statistical tests (default: 10000)

## License

This project is licensed under the MIT License.