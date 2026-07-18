# Predicting the Impact of Ball Milling on Particle Size Distribution

## Overview
This project implements a data science pipeline to predict particle size distribution (PSD) outcomes based on ball milling parameters using Gaussian Process Regression and Random Forest models.

## Prerequisites
- Python 3.11 or higher
- pip

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

3. (Optional) Install development tools:
 ```bash
 pip install -e ".[dev]"
 ```

## Project Structure
```
.
├── code/ # Source code
├── data/ # Data directories (raw, processed, splits)
├── tests/ # Test suite
├── results/ # Output artifacts
├── requirements.txt # Pinned dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## Usage
Refer to `quickstart.md` for execution instructions.

## License
MIT
