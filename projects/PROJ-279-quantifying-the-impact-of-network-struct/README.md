# PROJ-279: Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

This project implements a research pipeline to analyze the relationship between topological network structure and thermal conductivity in amorphous silicon (a-Si).

## Project Structure

- `code/`: Source code for the pipeline
 - `config/`: Environment and tooling configuration
 - `models/`: Data structures (AtomicConfiguration)
 - `*.py`: Core logic (download, validation, graph building, descriptors, regression)
- `data/`: Data storage
 - `raw/`: Downloaded MD trajectories
 - `processed/`: Graphs, descriptors, and analysis results
- `logs/`: Execution logs
- `state/`: Artifact versioning and checksums
- `tests/`: Unit and integration tests

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Configure environment:
 ```bash
 cp.env.example.env
 # Edit.env with your Zenodo URL and parameters
 ```
3. Run the pipeline:
 ```bash
 python code/main.py
 ```

## License

Research use only.
