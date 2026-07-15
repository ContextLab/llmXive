# PROJ-031: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

## Overview
This project analyzes the correlation between solar flare characteristics (GOES X-ray flux, CME speed) and geomagnetic storm intensities (Dst index).

## Project Structure
```
projects/PROJ-031-exploring-the-correlation-between-solar-/
├── code/ # Source code modules
│ ├── __init__.py
│ ├── ingest.py # Data ingestion
│ ├── align.py # Event alignment
│ ├── analysis.py # Statistical analysis
│ ├── validate.py # Schema validation
│ ├── versioning.py # Artifact versioning
│ ├── profiler.py # Performance profiling
│ └── setup_directories.py # Directory setup
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed and aligned data
├── results/ # Analysis results and metrics
├── contracts/ # Schema definitions
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run setup: `python code/setup_directories.py`

## Execution
Run the pipeline: `python code/main.py`

## Data Sources
- GOES X-ray flare lists: ftp://ftp.swpc.noaa.gov/pub/lists/
- CME catalog (SOHO/LASCO): CDAWeb
- Dst/Kp indices: NOAA SWPC

## License
Research project for scientific analysis.
