# Quickstart: Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity

## Prerequisites

- Python 3.11+
- `git`
- GitHub Actions runner (or local environment with sufficient RAM)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-086-exploring-the-impact-of-molecular-dynami
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins OpenMM, MDTraj, and pandas versions compatible with CPU-only execution.*

## Data Setup

The pipeline automatically downloads the PDBbind v2020 subset from the verified HuggingFace source.

```bash
# Run the data setup script (creates data/raw/ and downloads PDB files)
python code/utils/setup_data.py
```

*This script filters for complexes with resolution ≤ 2.0 Å and selects the first 10 valid entries.*

## Running the Pipeline

### Full Simulation & Analysis

Execute the entire workflow (Simulation → MM-PBSA → ANOVA):

```bash
python code/main.py --config code/simulation/config.yaml
```

**Expected Output**:
- `data/processed/energies.csv`
- `data/results/anova_results.json`
- `data/results/variance_plot.png`
- Console log with RMSE and ANOVA p-values.

### Individual Step Execution

1. **Run Simulations Only**:
   ```bash
   python code/simulation/run.py
   ```
   *Generates `.nc` files in `data/processed/trajectories/`.*

2. **Run MM-PBSA Only** (requires existing trajectories):
   ```bash
   python code/simulation/mm_pbsa.py
   ```
   *Generates `energies.csv`.*

3. **Run Statistical Analysis Only**:
   ```bash
   python code/analysis/stats.py
   ```
   *Generates ANOVA results and plots.*

## Verification

To verify the system works on a single complex (Acceptance Scenario 1):

```bash
python code/main.py --complex 1J22 --force-field ff14SB --duration 2ns --temp 300
```

**Success Criteria**:
- Job completes in < 7 minutes.
- `data/processed/trajectories/1J22_ff14SB_2ns_300.nc` exists.
- `data/processed/energies.csv` contains a row for 1J22.

## Troubleshooting

- **Memory Error**: Reduce the number of snapshots in `code/simulation/config.yaml` (default: 20).
- **Timeout**: The default CI limit is strict. If a run exceeds a predefined time threshold, it will be killed. Check `code/simulation/run.py` for the timeout handler.
- **Missing Atoms**: If MM-PBSA fails due to missing atoms, the complex is skipped. Check `logs/errors.log` for details.
