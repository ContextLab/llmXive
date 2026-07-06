# Quickstart: Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

## Prerequisites

- Python 3.11+
- Git
- A GitHub Actions runner (or local environment with 2+ CPU cores, 7 GB RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-279-quantifying-the-impact-of-network-struct
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Data Ingestion
Download the a-Si trajectories and verify checksums.
```bash
python code/download.py
```
*Output*: Files in `data/raw/`.

### 2. Graph Construction & Descriptor Calculation
Construct graphs and compute topological/vibrational descriptors.
```bash
python code/graph_builder.py --cutoffs 2.8 3.0 3.2
python code/descriptors.py
```
*Output*: Processed feature matrices in `data/processed/`.
*Note*: If pre-calculated VDOS is missing, the `VibrationalDescriptor` entity is omitted.

### 3. Model Training & Evaluation
Run Ridge and Random Forest regression with cross-validation.
```bash
python code/models.py
```
*Output*: `data/processed/results.csv`, model artifacts.
*Note*: If thermal conductivity is missing, the pipeline enters **Structure-Only Mode** and skips regression, outputting a "Partial Success" report.

### 4. Visualization
Generate scatter plots and feature importance charts.
```bash
python code/viz.py
```
*Output*: Figures in `data/processed/plots/`.

## Verification

Run the test suite to ensure correctness:
```bash
pytest tests/
```

## Troubleshooting

- **Checksum Mismatch**: If `download.py` fails, verify the Zenodo/HuggingFace URL in the config.
- **Memory Error**: If the dataset is too large, reduce the number of configurations processed or enable chunking in `code/download.py`.
- **Missing Thermal Conductivity**: If the dataset lacks target values, the pipeline will switch to **Structure-Only Mode** and report H-001/H-002 as "Untestable".
- **Missing VDOS**: If VDOS is not pre-calculated, the vibrational analysis is skipped, and the study proceeds with topological descriptors only.