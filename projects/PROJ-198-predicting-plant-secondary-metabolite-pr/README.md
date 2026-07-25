# llmXive: Predicting Plant Secondary Metabolite Profiles

This project implements an automated pipeline to predict plant secondary metabolite profiles
from genomic data using machine learning and phylogenetic analysis.

## Project Structure

```
.
 ├── code/ # Source code
 │ ├── data/ # Data download and preprocessing
 │ ├── models/ # Pydantic data models
 │ ├── utils/ # Utility functions
 │ ├── scripts/ # CLI scripts
 │ └── tests/ # Test suite
 ├── data/
 │ ├── raw/ # Raw downloaded data
 │ └── processed/ # Processed/aligned data
 ├── tests/ # Additional test resources
 ├── requirements.txt # Python dependencies
 ├── pyproject.toml # Project configuration
 └── README.md
```

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

3. Configure environment (optional):
 ```bash
 cp.env.example.env
 # Edit.env with your API keys and paths
 ```

## Usage

Run the main pipeline:
```bash
python code/scripts/main.py
```

Run tests:
```bash
pytest
```

## License

MIT License