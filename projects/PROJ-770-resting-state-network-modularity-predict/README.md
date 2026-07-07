# Resting-State Network Modularity Predicts Social Network Size

## Overview
This project investigates the relationship between resting-state fMRI network modularity and social network size using data from the Human Connectome Project (HCP).

## Project Structure
```
.
├── code/ # Source code for data processing and analysis
├── data/
│ ├── raw/ # Downloaded raw data (NIfTI, CSVs)
│ ├── processed/ # Intermediate processed data
│ └── results/ # Final analysis results
├── tests/ # Unit and integration tests
├── specs/ # Project specifications and design docs
├── requirements.txt # Python dependencies
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
Follow the tasks in `tasks.md` to execute the pipeline.
See `quickstart.md` for a step-by-step guide.

## Data Sources
Data is fetched from the Human Connectome Project (HCP) via S3 or HuggingFace.
Ensure you have the necessary credentials and permissions before running data download tasks.
