# PROJ-205: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

## Project Setup

This project uses Python 3.11.

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Code Quality Tools

This project uses **Black** for formatting and **Ruff** for linting.

To format code:
```bash
black code/
```

To check for linting issues:
```bash
ruff check code/
```

To automatically fix fixable linting issues:
```bash
ruff check --fix code/
```

Configuration is defined in `pyproject.toml`.

### Directory Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis scripts
│ ├── stimuli/ # HTML/CSS stimuli files
│ ├── survey/ # Streamlit survey application
│ └── utils/ # Utility functions
├── data/ # Data storage
│ ├── raw/ # Raw submission data
│ ├── processed/ # Processed analysis data
│ └── consent/ # IRB consent documents
├── tests/ # Test suite
├── docs/ # Documentation
├── pyproject.toml # Project configuration (Black, Ruff, dependencies)
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Execution

### Run the Survey
```bash
streamlit run code/survey/app.py
```

### Run Analysis
1. Preprocess data:
 ```bash
 python code/analysis/01_preprocess.py
 ```
2. Run ANOVA:
 ```bash
 python code/analysis/01_anova.py
 ```
3. Run Pairwise tests (if significant):
 ```bash
 python code/analysis/02_pairwise.py
 ```

## Contributing

Before committing, ensure code is formatted and passes linting:
```bash
black code/
ruff check --fix code/
```