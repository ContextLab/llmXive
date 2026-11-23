# PROJ-754: Linking Resting-State fMRI Entropy to Real-World Decision Risk-Taking

## Project Structure
- `src/`: Source code
 - `data/`: Data acquisition and preprocessing
 - `analysis/`: Entropy computation
 - `stats/`: Statistical modeling
 - `config/`: Configuration management
 - `utils/`: Utilities
 - `entities/`: Data models
- `tests/`: Test suites
- `data/`: Data artifacts (raw, cleaned, derived)
- `reports/`: Generated reports
- `docs/`: Documentation
- `scripts/`: Pipeline execution scripts
- `state/`: Pipeline state and checksums

## Setup
1. Ensure Python 3.11+
2. `pip install -r requirements.txt`
3. Set environment variable `HCP_TOKEN`
4. Run `python -m scripts.init_data_dirs` to initialize data directories
