# Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview
This project implements a reproducible scientific pipeline to quantify the relationship between dark matter halo shapes (triaxiality, axial ratios) and galaxy formation properties. The analysis leverages data from the TNG-100 simulation and, where available, Millennium-II.

**Key Features:**
- **Chunked Processing:** Designed to run on systems with limited RAM (7GB).
- **Robust Statistics:** Implements mass-matching, non-parametric tests, and Bonferroni correction.
- **Sensitivity Analysis:** Validates results against binning threshold variations.
- **Associational Flagging:** Explicitly marks all results as correlational.

## Project Structure
```
.
├── code/ # Source code
│ ├── ingestion/ # Data loaders (TNG, Millennium)
│ ├── processing/ # Physics calculations (Inertia, Shape, Alignment)
│ ├── analysis/ # Statistical tests and report generation
│ ├── utils/ # Configuration, I/O, Logging
│ └── tests/ # Unit and integration tests
├── data/
│ ├── raw/ # Downloaded simulation data
│ └── processed/ # Derived datasets (CSVs)
├── docs/ # Design and API documentation
├── paper/ # Research report templates
├── requirements.txt # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- A valid API key for the TNG Project (set as `TNG_API_KEY` environment variable).

### Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set the API key:
 ```bash
 export TNG_API_KEY="your_api_key_here"
 ```

### Running the Pipeline
Execute the main pipeline script:
```bash
python code/main.py
```

This will:
1. Fetch TNG-100 halo data (chunked).
2. Compute inertia tensors and shape metrics.
3. Perform statistical analysis (mass-matching, tests, regression).
4. Generate `data/processed/halo_shapes.csv` and `data/processed/statistical_results.csv`.

### Running Tests
```bash
pytest code/tests/
```

## Configuration
Edit `config.yaml` (in the project root) to adjust:
- `chunk_size`: Number of haloes per processing chunk.
- `min_particles`: Minimum particle count for valid haloes (default: 10,000).
- `binning_thresholds`: Thresholds for prolate/triaxial/spherical classification.

## Constraints & Limitations
- **RAM:** The pipeline assumes a maximum of 7GB RAM. Large simulations are processed in chunks.
- **Data:** If Millennium-II or WDM variants are not accessible, the pipeline logs the gap and proceeds with TNG-100 only.
- **Nature of Study:** All results are correlational (`associational_only=true`).

## License
This project is licensed under the MIT License.
