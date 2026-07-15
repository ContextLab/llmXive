# Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

This project investigates the application of unsupervised machine learning techniques, specifically Variational Autoencoders (VAEs), to detect and characterize phase transitions in isotropic spin systems (J1-J2 Heisenberg and XY models).

The pipeline generates synthetic Monte Carlo data, preprocesses spin configurations, trains a VAE to learn latent representations, and analyzes latent space variance to identify critical temperatures ($T^*$). Results are validated against magnetic susceptibility calculations and Finite-Size Scaling (FSS) theory.

## Project Structure

```text
.
├── code/ # Core implementation scripts
│ ├── config.py # Configuration management
│ ├── data_generation.py # Monte Carlo simulation (Metropolis-Hastings)
│ ├── preprocessing.py # Data normalization, reshaping, and splitting
│ ├── utils.py # Physics utilities (susceptibility, autocorrelation, FSS)
│ ├── vae_model.py # VAE architecture definition
│ ├── train.py # Training loop and early stopping
│ └── analysis.py # Latent space analysis and peak detection
├── data/
│ ├── raw/ # Raw spin configurations from simulations
│ └── processed/ # Normalized and split datasets
├── tests/
│ ├── unit/ # Unit tests for individual functions
│ ├── integration/ # End-to-end pipeline tests
│ └── contract/ # Schema validation tests
├── specs/001-gene-regulation/
│ └── contracts/ # YAML schemas for data and model artifacts
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### 1. Data Generation
Generate raw spin configurations for J1-J2 Heisenberg and XY models using the Metropolis-Hastings algorithm.
```bash
python code/data_generation.py
```
This will populate `data/raw/` with spin configurations for lattice sizes $L=16, 24$ and temperatures $T=0.1-3.0$.

### 2. Preprocessing
Normalize spins, reshape tensors, and perform stratified train/val splits.
```bash
python code/preprocessing.py
```
Output is saved to `data/processed/`.

### 3. Training
Train the Variational Autoencoder on the processed data.
```bash
python code/train.py
```
Checkpoints and logs are saved in `code/checkpoints/` and `code/logs/`.

### 4. Analysis
Analyze latent space variance to detect phase transitions and perform Finite-Size Scaling.
```bash
python code/analysis.py
```

## Testing

Run unit and integration tests:
```bash
python -m pytest tests/
```

## Configuration

Environment variables can be set in a `.env` file (if supported by your environment) or exported directly:
- `SEED`: Random seed for reproducibility (default: 42)
- `DATA_PATH`: Path to data directories
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## Contributing

Please ensure all code passes linting (`ruff`) and formatting (`black`) checks before submitting.

## License

[Insert License Information]