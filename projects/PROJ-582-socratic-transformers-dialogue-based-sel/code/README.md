# Socratic Transformers: Dialogue-Based Selection on Belief

## Project Setup

This project uses `ruff` for linting and `black` for formatting.

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

### Linting and Formatting

Run linting:
```bash
ruff check.
```

Run formatting:
```bash
black.
```

Run both (fix errors where possible):
```bash
ruff check. --fix
black.
```

### Testing

Run tests:
```bash
pytest
```
