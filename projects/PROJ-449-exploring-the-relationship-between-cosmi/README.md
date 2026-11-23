# Cosmic Ray Composition vs Solar Activity Analysis

Automated research pipeline to explore the relationship between cosmic ray composition
and solar activity cycles using AMS-02 and NOAA data.

## Requirements

- Python 3.11+
- System dependencies: None (pure Python stack)

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Correlation, bootstrap, model fitting
│ ├── data/ # Data fetching and preprocessing
│ ├── utils/ # Utilities (config, logging)
│ └── main.py # Pipeline entry point
├── data/ # Data storage
│ ├── raw/ # Downloaded raw data
│ └── processed/ # Processed datasets and results
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── pyproject.toml # Project configuration
```

## Usage

Run the full pipeline:
```bash
python -m code.main
```

Run tests:
```bash
pytest
```

## Data Sources

- **AMS-02**: Cosmic ray flux data (protons, helium, CNO, Fe)
- **NOAA/SWPC**: Daily sunspot numbers

See `code/utils/config.py` for specific data URLs and configuration.

## License

Research project - data available under respective source licenses.
