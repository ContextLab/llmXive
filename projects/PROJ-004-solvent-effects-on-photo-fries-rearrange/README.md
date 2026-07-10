# PROJ-004: Solvent Effects on Photo-Fries Rearrangement

Automated research pipeline for analyzing solvent polarity effects on singlet-radical-pair intermediate lifetimes in aryl ester Photo-Fries rearrangement.

## Project Structure

- `code/`: Source code for analysis, data loading, and hardware interfaces.
- `data/`: Data storage (raw, compute, processed, chemicals).
- `tests/`: Unit and integration tests.
- `docs/`: Documentation and methodology notes.
- `figures/`: Generated plots and visualizations.
- `paper/`: Manuscript drafts and tables.

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the pipeline:
 ```bash
 python code/main.py --help
 ```

## Configuration

Edit `data/chemicals/solvents.yaml` to define solvent properties.
Modify `code/config.py` if path structures need adjustment.

## License

MIT
