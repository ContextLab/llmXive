# llmXive: Network Structure & Neural Avalanche Dynamics

## Project Overview

This project investigates the relationship between structural connectome properties (network structure) and neural avalanche dynamics (criticality) using a combination of real dMRI/EEG data and Wilson-Cowan simulations.

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
pip install -r code/requirements.txt
```

### Configuration
Create a `.env` file in the project root:
```
DATA_ROOT=./data
SIMULATION_SEED=42
LOG_LEVEL=INFO
```

### Running the Pipeline
```bash
python code/main.py
```

## Documentation

- **[Data Model](001_data_model.md)**: Definitions of Participant, StructuralConnectome, and AvalancheRecord.
- **[API Usage](002_api_usage.md)**: How to use the core modules.
- **[Architecture](003_architecture.md)**: System design and data flow.
- **[Data Integrity](004_data_integrity.md)**: Protocols for reproducibility and real-data enforcement.

## Task Status

- **Phase 1 (Setup)**: Complete
- **Phase 2 (Foundational)**: Complete
- **Phase 3 (Data Pipeline)**: Complete (Simulation Primary Path)
- **Phase 4 (Metrics)**: Complete
- **Phase 5 (Stats)**: Complete
- **Phase 6 (Revision)**: Complete
- **Phase 7 (Polish)**: In Progress

## Contributing

See `tasks.md` for the current implementation backlog.
Ensure all new code adheres to the "Fail Loudly" and "Real Data Only" principles.