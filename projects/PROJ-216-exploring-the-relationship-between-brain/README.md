# Exploring the Relationship Between Brain Network Dynamics and Musical Creativity

## Project Overview

This project investigates the relationship between functional brain network dynamics and measures of cognitive performance (specifically Fluid Intelligence as a proxy for creative potential). We utilize resting-state fMRI data from the OpenNeuro datasets `ds000224` and `ds000230` to construct brain graphs, compute topological metrics, and correlate these with behavioral scores.

## Key Features

- **Data Ingestion**: Automated download and validation of OpenNeuro fMRI datasets.
- **Preprocessing**: Pipeline for motion correction, normalization, and bandpass filtering using FSL/AFNI.
- **Graph Analysis**: Computation of global efficiency, clustering coefficient, and modularity using the Schaefer parcellation atlas.
- **Statistical Analysis**: Correlation analysis with Bonferroni correction and effect size estimation (Cohen's d).
- **Resource Monitoring**: Tracking of RAM usage and runtime for reproducibility.

## Prerequisites

- Python 3.11+
- System dependencies: FSL, AFNI (required for preprocessing)
- External data: OpenNeuro datasets `ds000224` and `ds000230`

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-216-exploring-the-relationship-between-brain
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Verify system dependencies (FSL/AFNI):
 ```bash
 python code/dependency_check.py
 ```

## Quickstart

Follow the step-by-step guide in `quickstart.md` to run the full pipeline:
1. Setup directories
2. Download and validate data
3. Preprocess fMRI data
4. Compute graph metrics
5. Perform statistical analysis
6. Generate reports

## Project Structure

```
.
├── code/ # Source code modules
│ ├── __init__.py
│ ├── config.py # Configuration management
│ ├── download.py # Data ingestion from OpenNeuro
│ ├── preprocess.py # fMRI preprocessing pipeline
│ ├── graph_metrics.py # Graph theory calculations
│ ├── stats.py # Statistical analysis
│ ├── utils.py # Utilities (ResourceMonitor)
│ └──... # Other helper scripts
├── data/ # Data storage
│ ├── raw/ # Downloaded raw data
│ ├── interim/ # Intermediate processing files
│ └── processed/ # Final processed data and metrics
├── reports/ # Generated reports and figures
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Step-by-step execution guide
```

## Execution

To run the full pipeline from start to finish:

```bash
# 1. Setup
python code/setup_directories.py

# 2. Download Data
python code/download.py

# 3. Preprocess
python code/preprocess.py

# 4. Graph Metrics
python code/aggregate_graph_metrics.py

# 5. Stats & Effect Sizes
python code/stats.py
python code/calculate_effect_sizes.py

# 6. Visualization & Reporting
python code/generate_scatter_plots.py
python code/generate_analysis_resource_profile.py
```

## License

This project is licensed under the MIT License.

## Contributing

Please read the contribution guidelines before submitting pull requests.
