# PROJ-328: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

## Project Structure

This project follows the following directory structure:

```
projects/PROJ-328-predicting-the-impact-of-composition-on-/
├── data/
│ ├── raw/ # Raw ingested data
│ ├── processed/ # Processed and validated data
│ ├── outputs/ # Generated outputs (plots, reports)
│ └── checksums/ # Data checksums
├── code/
│ ├── ingestion/ # Data ingestion pipeline
│ ├── features/ # Feature engineering
│ ├── models/ # Model definitions and training
│ ├── evaluation/ # Model evaluation
│ ├── visualization/ # Plot generation
│ └── utils/ # Utility functions
├── tests/
│ ├── contract/ # Contract tests
│ ├── integration/ # Integration tests
│ └── unit/ # Unit tests
├── models/ # Saved model artifacts
└── specs/ # Feature specifications

## Setup

To set up the project structure, run:

```bash
python code/setup_project_structure.py
```

## Requirements

Install dependencies:

```bash
pip install -r code/requirements.txt
```

## Running the Pipeline

1. Ingest data: `python code/ingestion/pipeline_runner.py`
2. Train models: `python code/features/descriptor_engine_main.py`
3. Evaluate: `python code/evaluation/bootstrap.py`
4. Visualize: `python code/visualization/...`

## License

MIT License
