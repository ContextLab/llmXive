# The Impact of Linguistic Complexity on Trust in AI-Generated Text

## Overview

This project investigates the relationship between linguistic complexity metrics
(Flesch-Kincaid, MTLD, average sentence length) and human trust ratings in
AI-generated text. The pipeline generates AI text samples, collects human trust
ratings via Prolific, and performs statistical analysis to test the inverted-U
hypothesis.

## Installation

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-521-the-impact-of-linguistic-complexity-on-t
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

4. Configure linting and formatting:
 ```bash
 # Install pre-commit hooks (optional)
 pre-commit install
 ```

## Usage

### Data Generation (User Story 1)

```bash
python code/generate_text.py
```

This generates `data/raw/generated_text.csv` with linguistic complexity metrics.

### Trust Rating Collection (User Story 2)

```bash
python code/collect_trust.py
```

This collects trust ratings from participants and saves to `data/raw/trust_responses.csv`.

### Statistical Analysis (User Story 3)

```bash
python code/analyze.py
```

This performs regression analysis and saves results to `data/outputs/`.

## Project Structure

```
projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/
├── code/
│ ├── utils.py # Metric computation utilities
│ ├── generate_text.py # Text generation script
│ ├── collect_trust.py # Trust rating collection
│ ├── analyze.py # Statistical analysis
│ └── requirements.txt # Dependencies
├── data/
│ ├── raw/ # Raw generated and collected data
│ ├── processed/ # Cleaned and processed data
│ └── outputs/ # Analysis results and figures
├── tests/
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema validation tests
├── specs/
│ └── 001-linguistic-complexity-trust/
│ └── contracts/ # JSON schemas
├── README.md
├── pyproject.toml # Project configuration (Black, Ruff)
└──.ruff.toml # Ruff configuration
```

## Configuration

### Linting and Formatting

The project uses:
- **Black** for code formatting (88 char line length)
- **Ruff** for linting (PEP8, Pyflakes, etc.)

Run checks:
```bash
ruff check code/
black --check code/
```

Format code:
```bash
black code/
ruff check --fix code/
```

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run contract tests:
```bash
pytest tests/contract/
```

Run integration tests:
```bash
pytest tests/integration/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## License

MIT License