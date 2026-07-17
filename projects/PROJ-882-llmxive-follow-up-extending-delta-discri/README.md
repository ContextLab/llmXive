# llmXive Follow-up: Extending DelTA

Automated science pipeline for Discriminative Token Credit Assignment for Reinforcement Learning.

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -e.
 ```
3. Install spaCy model:
 ```bash
 python -m spacy download en_core_web_sm
 ```

## Linting and Formatting

This project uses **Black** for formatting and **Ruff** for linting.

### Running Black
```bash
black code/ tests/
```

### Running Ruff
```bash
ruff check code/ tests/
```

### Running Checks in CI
The CI pipeline (GitHub Actions) will automatically run these checks on pull requests.

## Project Structure
```
code/
 config.py
 main.py
 data/
 download_gsm8k.py
 generate_oracle.py
 extract_features.py
 save_oracle_results.py
 models/
 mlp.py
 train.py
 eval/
 metrics.py
 interpret.py
data/
 raw/
 processed/
contracts/
tests/
```

## Usage
Run the full pipeline:
```bash
python code/main.py
```

## License
MIT