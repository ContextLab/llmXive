# Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

## Project Overview
This project implements an automated science pipeline to predict the glass transition temperature (Tg) of chalcogenide glasses based on their chemical composition.

## Prerequisites
- Python 3.11+
- pip

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

3. Run the setup script to create directory structure:
 ```bash
 python code/setup_directories.py
 ```

## Project Structure
```
.
├── code/
│ ├── setup_directories.py
│ ├── setup_project_structure.py
│ ├── src/
│ │ ├── data/
│ │ │ ├── download.py
│ │ │ ├── init_manifest.py
│ │ │ ├── preprocess.py
│ │ │ └── split.py
│ │ ├── models/
│ │ └── utils/
│ │ ├── constants.py
│ │ ├── logger.py
│ │ ├── manifest_manager.py
│ │ └── metrics.py
│ └── tests/
│ ├── unit/
│ └── integration/
├── data/
├── artifacts/
├── state/
├── specs/
├── requirements.txt
├──.flake8
├── pyproject.toml
└── README.md
```

## Running the Pipeline
Follow the tasks in `tasks.md` to execute the pipeline step by step.

## License
MIT
