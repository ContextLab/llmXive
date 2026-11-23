# PROJ-364: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

## Project Structure
- `src/`: Source code for data ingestion, graph construction, and analysis.
- `tests/`: Unit and integration tests.
- `data/raw/`: Raw input datasets (defect coordinates, thermal conductivity).
- `data/processed/`: Processed data (graphs, metrics).
- `results/`: Final analysis results and visualizations.
- `state/`: Intermediate state and status flags (e.g., data availability).
- `contracts/`: Schema definitions for data validation.
- `logs/`: Execution logs.
- `docs/`: Documentation.

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the setup script to verify structure:
 ```bash
 python setup_structure.py
 ```

## Configuration
Edit `config.yaml` to set material constants, thresholds, and analysis parameters.