# Data Model: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## 1. Entity Definitions

### 1.1 SpinConfiguration
Represents a single snapshot of the isotropic spin system.
*   **Attributes**:
    *   `lattice_size` (int): Size $L$ of the square lattice.
    *   `temperature` (float): Simulation temperature $T$ (in units of $J$).
    *   `model_type` (str): "Heisenberg" or "XY".
    *   `spins` (ndarray): Tensor of shape `(3, L, L)` for Heisenberg or `(2, L, L)` for XY.
    *   `metadata`: Dictionary containing simulation parameters (seeds, steps).

### 1.2 LatentRepresentation
The compressed vector output from the VAE encoder.
*   **Attributes**:
    *   `temperature` (float): The temperature of the input configuration.
    *   `mu` (ndarray): Mean vector of shape `(10,)`.
    *   `sigma` (ndarray): Log-variance vector of shape `(10,)`.
    *   `z` (ndarray): Sampled latent vector of shape `(10,)`.

### 1.3 CriticalSignature
Derived metric indicating the phase transition.
*   **Attributes**:
    *   `t_star` (float): Detected critical temperature.
    *   `variance_peak` (float): Magnitude of the variance peak.
    *   `confidence_interval` (tuple): (lower, upper) 95% CI.
    *   `susceptibility_t_max` (float): Temperature of max susceptibility (ground truth).
    *   `fss_extrapolated_tc` (float): Extrapolated $T_c$ for $L \to \infty$.

### 1.4 ModelCheckpoint
Metadata for the trained VAE model.
*   **Attributes**:
    *   `model_type` (str): "Heisenberg" or "XY".
    *   `architecture_hash` (str): SHA-256 of the architecture definition.
    *   `hyperparameters` (dict): Learning rate, epochs, etc.
    *   `checksum` (str): SHA-256 of the binary `.pt` file.
    *   `created_at` (str): ISO timestamp.

## 2. Data Flow

1.  **Input**: Raw simulation parameters (Model, L, T, Seed).
2.  **Generation**: `data_generation.py` produces `SpinConfiguration` objects.
3.  **Preprocessing**: `preprocessing.py` normalizes and reshapes to `[batch, channels, L, L]`.
4.  **Encoding**: `vae_model.py` produces `LatentRepresentation` for each sample.
5.  **Aggregation**: `analysis.py` computes variance per temperature bin.
6.  **Output**: `CriticalSignature` stored in JSON/CSV. `ModelCheckpoint` metadata stored in JSON.

## 3. Storage Format

*   **Raw Data**: `.npy` files (NumPy arrays) in `data/raw/`.
*   **Processed Data**: `.npy` files in `data/processed/`.
*   **Models**: `.pt` (PyTorch) in `models/`. Metadata stored in `models/metadata.json` validated against `model-checkpoint.schema.yaml`.
*   **Results**: `.json` in `data/results/`.
