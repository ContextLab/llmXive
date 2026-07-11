# llmXive: Predicting Plant Secondary Metabolite Profiles

This project implements a pipeline to predict plant secondary metabolite profiles from genomic data using machine learning and phylogenetic methods.

## Project Structure

```
.
├── code/ # Source code
│ ├── data/ # Data download and preprocessing
│ ├── models/ # Pydantic data models
│ ├── modeling/ # ML and statistical modeling
│ ├── utils/ # Utility functions
│ └── scripts/ # CLI scripts
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed/aligned data
│ └── interim/ # Intermediate data
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── README.md
```

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Configure environment:
 ```bash
 cp.env.example.env
 # Edit.env with your API keys
 ```

3. Run tests:
 ```bash
 pytest
 ```

## Usage

See `docs/` for detailed usage instructions.
