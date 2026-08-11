# Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## Project Overview

This research project investigates the ability of unsupervised machine learning (specifically Variational Autoencoders) to detect phase transitions in isotropic spin systems (2D J1-J2 Heisenberg and XY models) without prior knowledge of the critical temperature.

The pipeline generates Monte Carlo simulation data, preprocesses spin configurations, trains a VAE, and analyzes the latent space variance to identify pseudo-critical temperatures ($T^*$). Results are validated against magnetic susceptibility calculations and finite-size scaling (FSS) extrapolations.

## Key Features

- **Data Generation**: Metropolis-Hastings algorithm for J1-J2 Heisenberg and XY models.
- **Unsupervised Learning**: VAE architecture with 2 convolutional layers and latent dimension 10.
- **Physical Verification**: Calculation of magnetic susceptibility ($\chi$) and autocorrelation times ($\tau_{int}$).
- **Robust Analysis**: Gaussian Process smoothing for peak detection, bootstrap confidence intervals, and FSS extrapolation.
- **Reproducibility**: Full pipeline logging, seed pinning, and checksum verification.

## Prerequisites

- Python 3.11+
- pip
- Linux/macOS environment (recommended for performance)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Setup environment variables** (optional):
 Create a `.env` file in the root directory based on `.env.example` if custom paths or logging levels are needed.
 ```bash
 cp.env.example.env
 ```

## Project Structure

```text
.
├── code/ # Source code for the pipeline
│ ├── data_generation.py # Monte Carlo simulation
│ ├── preprocessing.py # Data normalization and splitting
│ ├── vae_model.py # VAE architecture
│ ├── train.py # Training loop
│ ├── analysis.py # Latent space analysis & FSS
│ └── utils.py # Physics utilities (susceptibility, etc.)
├── data/
│ ├── raw/ # Raw Monte Carlo spin configurations
│ └── processed/ # Preprocessed tensors
├── results/ # Output reports, CSVs, and JSONs
├── specs/001-gene-regulation/contracts/ # Schema definitions
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage

### 1. Data Generation
Generate raw spin configurations for the J1-J2 Heisenberg and XY models.
```bash
python code/data_generation.py --model heisenberg --lattice 16 --temp-range 0.1 3.0
python code/data_generation.py --model xy --lattice 24 --temp-range 0.1 3.0
```

### 2. Preprocessing
Normalize spins, reshape, and split into train/validation sets.
```bash
python code/preprocessing.py
```

### 3. VAE Training
Train the unsupervised model on the preprocessed data.
```bash
python code/train.py --epochs 100 --lr 1e-3
```

### 4. Analysis
Perform latent variance analysis, peak detection, and finite-size scaling.
```bash
python code/analysis.py
```

### 5. Full Pipeline
Run the entire workflow from generation to report.
```bash
bash run_all.sh
```

## Validation & Testing

Run the unit tests to verify the pipeline integrity:
```bash
python -m pytest tests/unit/ -v
```

Run integration tests:
```bash
python -m pytest tests/integration/ -v
```

## Configuration

The project uses `config.py` and `env_setup.py` for configuration management. Random seeds are pinned to ensure reproducibility. See `.env.example` for available settings.

## Limitations

- Current implementation supports CPU execution only.
- Lattice sizes are limited to L=16 and L=24 due to memory constraints (6 GB RAM limit).
- Finite-size scaling is performed with limited data points (2 lattice sizes), which may result in "FSS Inconclusive" status for some models.

## Future Work

- GPU acceleration for training and simulation.
- Expansion to larger lattice sizes (L=32, 64).
- Integration of additional isotropic models.

## License

This project is part of the llmXive automated science pipeline.