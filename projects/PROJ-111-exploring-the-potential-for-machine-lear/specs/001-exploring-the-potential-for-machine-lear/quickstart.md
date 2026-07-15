# Quickstart: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local environment with 2+ CPU cores, 8GB RAM).

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
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with the free-tier runner.*

## Execution Workflow

### Step 1: Generate Data (Optional if pre-computed)
If no pre-computed data exists, run the generation script:
```bash
python code/data_generation.py --model Heisenberg --L 16,24 --T_range 0.1 3.0 0.1
```
*Output: `data/raw/` with `.npy` files.*

### Step 2: Preprocess Data
```bash
python code/preprocessing.py --input data/raw/ --output data/processed/
```
*Output: Normalized tensors in `data/processed/`.*

### Step 3: Train VAE
```bash
python code/train.py --data data/processed/ --epochs 50 --seed 42
```
*Output: `models/vae_heisenberg.pt` and training logs.*

### Step 4: Analyze & Detect Transition
```bash
python code/analysis.py --model models/vae_heisenberg.pt --data data/processed/
```
*Output: `data/results/critical_signature.json` containing $T^*$, CI, and FSS results.*

## Validation

Run the test suite to ensure contract compliance:
```bash
pytest tests/ -v
```
*Checks: Data shapes, VAE convergence, Peak detection logic, Schema validation.*

## Troubleshooting

*   **Memory Error**: Reduce batch size in `train.py` or sample fewer configurations in `data_generation.py`.
*   **Timeout**: If running on CI, check if "Time Budget Exceeded" flag is set. The script will output partial results.
*   **No Peak Detected**: Check `data/results/analysis.log` for "No significant transition detected". Verify temperature range and sampling density.
