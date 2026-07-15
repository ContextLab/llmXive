# Quickstart: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## Prerequisites

- Python 3.11+
- Git
- Access to a HuggingFace account (optional, for dataset access)
- Substantial RAM, Substantial disk capacity (local or CI)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Simulation

### 1. Run a Single Experiment
To run a single experiment with low-bit precision and a fixed random seed:
```bash
python -m simulation.training_loop --bit-width 4 --seed 42 --clips 20
```
- `--bit-width`: Target precision (2, 3, 4, 5, or 6).
- `--seed`: Random seed.
- `--clips`: Number of clips to process (default: 20, adjusted for 5 bit-widths).

### 2. Run the Full Experimental Suite
To run all experiments across multiple bit-widths and seeds:
```bash
python -m analysis.aggregation --full-suite
```
This will:
- Run the simulation for each bit-width and seed.
- Evaluate the generated clips.
- Aggregate results into `data/derived/results.csv`.
- Generate the precision-consistency curve plot.

### 3. Validate Quantization Emulation
To verify the noise distribution:
```bash
python -m tests.test_quantization_emulator
```

## Expected Output

- **Console**: Progress bars, memory usage estimates, and final scores.
- **Files**:
  - `data/derived/results.csv`: Aggregated results.
  - `data/derived/figures/precision_consistency_curve.png`: Visualization of the threshold.
  - `data/derived/figures/noise_distribution.png`: KL-divergence test results.

## Troubleshooting

- **Memory Error**: Reduce the `--clips` parameter or the model size in `config.py`.
- **Dataset Access Error**: Ensure you have internet access and the HuggingFace `kinetics-400` dataset is available. If not, the script will abort with a clear error or fallback to UCF.
- **CUDA Error**: Ensure no GPU-specific code is executed. The script should run on CPU only.
