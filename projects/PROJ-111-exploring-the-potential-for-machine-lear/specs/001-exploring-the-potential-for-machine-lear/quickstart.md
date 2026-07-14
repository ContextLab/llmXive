# Quickstart: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## Prerequisites

*   Python 3.10+
*   `pip`
*   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-111-exploring-the-potential-for-machine-lear
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

The entire pipeline can be executed via the main entry point. This script handles data generation, training, and analysis in sequence.

```bash
python code/main.py
```

### Configuration

You can override default parameters by editing `code/config.py` or passing arguments:

```bash
python code/main.py --lattice 16 --epochs 50 --model heisenberg
```

### Steps Explained

1.  **Data Generation**: The script generates Monte Carlo configurations for the specified model and lattice size.
2.  **Preprocessing**: Data is normalized, split into train/validation sets, and checksummed.
3.  **Training**: The VAE is trained on CPU. Progress is logged to the console.
4.  **Analysis**: Latent space variance (reconstruction error) is calculated, Savitzky-Golay smoothing is applied, and the critical temperature is identified.
5.  **Validation**: Magnetic susceptibility is computed, FSS is performed to extrapolate $T_c(\infty)$, and the ML result is compared against this ground truth.

## Output

Results are saved to the `results/` directory:
*   `latent_variance.csv`: Variance of reconstruction error per temperature.
*   `critical_signature.json`: Final $T^*$, confidence intervals, and validation metrics.
*   `plots/`: Visualizations of the latent space, susceptibility, and peak detection.

## Troubleshooting

*   **Memory Error**: Reduce `--samples-per-bin` in `config.py`.
*   **Training Timeout**: The script will auto-stop if it exceeds 6 hours. Reduce `--epochs` or `--lattice` size.
*   **No Peak Detected**: Check `results/latent_variance.csv`. If the curve is flat, the VAE may not have learned the physics. Try increasing `latent_dim` or `epochs`.
*   **Autocorrelation Warning**: If `tau_int` is very large, the script may reduce the number of effective samples. Ensure sufficient simulation time.