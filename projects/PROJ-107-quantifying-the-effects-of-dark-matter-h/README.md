# llmXive Research Pipeline: Quantifying Dark Matter Halo Shapes

This project implements an automated science pipeline to quantify the effects of dark matter halo shapes on galaxy formation using TNG-100 and Millennium-II simulation data.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis modules
│ ├── ingestion/ # Data loading modules
│ ├── processing/ # Data processing modules
│ ├── tests/ # Unit and integration tests
│ ├── utils/ # Utility modules (config, logging, io)
│ └── main.py # Pipeline entry point
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data outputs
│ └── metadata.yaml # Data metadata and checksums
├── outputs/ # Pipeline outputs
│ ├── logs/ # Execution logs
│ └── figures/ # Generated plots
├── tests/ # Additional test infrastructure
├──.ruff.toml # Linting configuration
├── pyproject.toml # Project configuration and dependencies
└── README.md # This file
```

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

3. Configure the pipeline:
 - Update `data/metadata.yaml` with any required API keys or paths
 - Ensure sufficient disk space for TNG-100 data (~100GB+)

## Usage

Run the full pipeline:
```bash
python code/main.py
```

Run specific tasks:
```bash
python code/main.py --task T006 # Run logging infrastructure setup
```

Run tests:
```bash
pytest code/tests/
```

## Hardware Constraints

This pipeline is designed to run on systems with limited resources:
- **RAM**: 7GB maximum
- **CPU**: Multi-core CPU (no GPU required)
- **Disk**: ~100GB for raw data, ~10GB for processed outputs

To accommodate these constraints, the pipeline implements:
- Chunked data processing
- Sampling strategies for large datasets
- Memory-efficient data structures

## Logging

The pipeline includes comprehensive logging infrastructure:
- All logs are written to `outputs/logs/pipeline_<timestamp>.log`
- Console output shows INFO level and above
- File output includes DEBUG level details
- Metrics, errors, and task progress are automatically logged

## License

This research pipeline is provided for academic purposes.
See project specifications for detailed licensing information.