# PROJ-107: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## Hardware Constraints & Deviations
**Important**: This project is designed to run on machines with limited resources (specifically **7GB RAM** and CPU-only execution).

Due to these hardware constraints, the pipeline implements **chunked processing** and **sampling**. This is a documented deviation from the original requirement FR-001 ("process every FoF halo") to satisfy Success Criterion SC-005 (Feasibility).

- **Chunked I/O**: Data is read and processed in small chunks to prevent memory overflow.
- **Sampling**: If a snapshot exceeds memory limits even with chunking, a representative sample is processed.
- **No GPU**: All computations are performed on CPU.

## Project Structure
- `code/`: Source code for the pipeline
- `data/`: Raw and processed data artifacts
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents

## Installation
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
Run the main pipeline:
```bash
python code/main.py
```

Run tests:
```bash
pytest code/tests/
```

## Output
The primary output for User Story 1 is `data/processed/halo_shapes.csv`, containing axial ratios, triaxiality, and other shape metrics for valid haloes.
