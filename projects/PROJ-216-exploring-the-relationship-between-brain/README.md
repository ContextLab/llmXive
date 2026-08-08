# llmXive: Brain Network Dynamics and Musical Creativity

## Project Setup

### Prerequisites
- Python 3.9+
- pip
- FSL and AFNI (for preprocessing tasks)

### Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmxive-brain-music
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -e.
 ```

### Code Quality Tools

This project uses **Black** for code formatting and **Ruff** for linting.

To install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

To run manually:
```bash
# Format code
black code/

# Lint code
ruff check code/
```

### Directory Structure

- `code/`: Source code
- `data/raw`: Raw data from OpenNeuro
- `data/interim`: Intermediate processed data
- `data/processed`: Final processed data
- `tests/`: Test suites
- `reports/`: Generated reports and figures
