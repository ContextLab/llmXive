# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Structure

This project analyzes the correlation between bird migration phenology and climate variables using eBird and NOAA data.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create and activate a virtual environment:
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

## Pre-commit Configuration

This project uses `pre-commit` to enforce code quality standards automatically before each commit.

The following hooks are configured:
- **Black**: Code formatting (line-length=88, target-version=py311)
- **Ruff**: Linting (checks for E, F, W, I errors) and formatting

To manually run all hooks on all files:
```bash
pre-commit run --all-files
```

To update hooks to their latest versions:
```bash
pre-commit autoupdate
```

## Usage

### Running the Pipeline

Execute the full analysis pipeline:
```bash
python run_pipeline.py
```

### Data Preparation

Download and prepare raw data:
```bash
python src/data/download.py
```

### Preprocessing

Run data preprocessing:
```bash
python src/data/preprocess.py
```

### Modeling

Fit GAMM models and perform analysis:
```bash
python src/models/gamm_fit.py
```

## Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test types:
```bash
pytest tests/unit/ # Unit tests
pytest tests/integration/ # Integration tests
pytest tests/contract/ # Contract tests
```

## Configuration

Configuration parameters can be set in `src/lib/config.py`:
- `SEED`: Random seed for reproducibility (default: 42)
- `GRID_RES`: Grid resolution in degrees (default: 0.5)
- `SAMPLE_SIZE`: Sample size for analysis
- `PERMUTATIONS`: Number of permutations for tests (default: 10000)

## License

[License information]

## Contributing

Please read our contributing guidelines before submitting pull requests.