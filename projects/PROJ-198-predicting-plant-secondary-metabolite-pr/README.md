# PROJ-198: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Overview
This project implements a pipeline to predict plant secondary metabolite profiles using genomic data, specifically focusing on the relationship between Biosynthetic Gene Clusters (BGCs) and metabolite abundance.

## Project Structure
```
PROJ-198/
├── code/ # Source code
│ ├── data/ # Data loading and preprocessing
│ ├── modeling/ # Machine learning models
│ └── utils/ # Utilities (phylogeny, parsing)
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed datasets
├── tests/ # Test suite
│ ├── unit/
│ ├── integration/
│ └── contract/
├── requirements.txt # Dependencies
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

## Usage
See `quickstart.md` for the end-to-end pipeline execution guide.

## License
MIT
