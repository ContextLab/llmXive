# llmXive Follow-up: Extending "Geometric Action Model for Robot Policy Learning"

## Project Structure

This project implements a symbolic-latent planner to extend the Geometric Action Model (GFM) for robot policy learning.

### Directory Layout

- `code/`: Core Python modules (GFM wrapper, symbolic solver, analysis, etc.)
- `data/`: Data storage
 - `raw/`: Original datasets and baseline metadata
 - `generated/`: Synthetic test sets and intermediate simulation data
 - `results/`: Final experiment results and statistical reports
- `tests/`: Unit and integration tests
- `scripts/`: Executable scripts for generation, inference, and analysis
- `specs/`: Feature specifications and design documents
- `projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/`: This project root

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

## Usage

Refer to individual scripts in the `scripts/` directory for usage instructions.
