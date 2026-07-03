# Quickstart: Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

## Prerequisites

- Python 3.11+
- Git
- 2 CPU cores, ≥7 GB RAM, ≥14 GB disk (GitHub Actions free-tier compatible)
- (Optional) Pre-equilibrated amorphous silicon XYZ files in `data/raw/`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-366-quantifying-the-influence-of-network-top
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

   *Note: `requirements.txt` pins CPU-only versions of PyTorch, PyTorch Geometric, and `ase`.*

## Data Preparation

### Option A: Use Provided Data
If you have pre-equilibrated XYZ files:
1. Place them in `data/raw/` (e.g., `sample_1.xyz`, `sample_2.xyz`, ...).
2. Ensure filenames follow the pattern `sample_N.xyz` (N ≥ 2).

### Option B: Generate Synthetic Data
If no data is provided, run the sample generator:
```bash
python code/ingest/sample_generator.py --num-samples 2 --output-dir data/raw/
```
*This will generate 2 synthetic samples via melt-quench protocol (may take [deferred]).*

## Running the Pipeline

### Step 1: Graph Construction
```bash
python code/ingest/graph_builder.py --input-dir data/raw/ --output-dir data/processed/graphs/ --cutoff 3.0
```
*Verifies edge counts and node-degree distribution (US-1).*

### Step 2: Green-Kubo Simulation
```bash
python code/simulation/green_kubo.py --input-dir data/raw/ --output-dir data/processed/conductivities/ --config code/simulation/config.yaml
```
*Runs LAMMPS simulations; checks convergence (SC-003).*

### Step 3: Topological Metric Extraction
```bash
python code/metrics/topology_extractor.py --input-dir data/processed/graphs/ --output-dir data/processed/metrics/
```
*Computes degree, clustering, shortest-path statistics and their variances (FR-002).*

### Step 4: GNN Training
```bash
python code/model/trainer.py --data-dir data/processed/ --output-dir data/processed/model_outputs/ --epochs 60
```
*Trains 2-layer GNN to predict Static Scattering Potential; checks convergence (SC-002).*

### Step 5: LMM Analysis
```bash
python code/analysis/lmm_analysis.py --data-dir data/processed/ --output-file data/processed/correlation_results.json
```
*Performs Linear Mixed-Effects Model analysis; outputs coefficients and p-values (FR-005).*

## Verification

1. **Check convergence**:
   ```bash
   grep "convergence_flag" data/processed/conductivities/*.json
   ```
   *All included samples should have `convergence_flag: true`.*

2. **Check statistical results**:
   ```bash
   cat data/processed/correlation_results.json
   ```
   *Look for `lmm_coefficients` and `lmm_p_values`.*

3. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## Troubleshooting

- **Runtime exceeds 6 hours**: Reduce the number of samples (N) or trajectory length in `code/simulation/config.yaml`.
- **Green-Kubo non-convergence**: Increase simulation time or check `exclusion_flag` in results.
- **GNN training fails**: Ensure `N ≥ 2` samples; check for NaN in input features.
- **Missing data**: Run `code/ingest/sample_generator.py` to generate synthetic samples.