# llmXive: GateMem Benchmark Extension

Automated science pipeline for benchmarking memory governance in multi-principal shared-memory systems.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Install dev tools:
 ```bash
 pip install -e ".[dev]"
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── cli/
│ ├── data/
│ ├── gatekeeper/
│ ├── models.py
│ └── utils/
├── data/ # Data artifacts (raw, processed, samples)
├── tests/ # Test suite
├── contracts/ # Schema definitions
├── specs/ # Design documents
├── requirements.txt # Dependencies
├── pyproject.toml # Build & tool config
└── README.md
```

## Quickstart

See `quickstart.md` for detailed execution instructions.

## License

MIT
