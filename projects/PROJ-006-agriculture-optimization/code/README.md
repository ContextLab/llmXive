# Climate-Smart Agricultural Optimization Project (PROJ-006)

## Overview
This project implements a research pipeline to analyze the correlation between
Climate-Smart Agricultural (CSA) practices and yield stability, independent of
financial access.

## Structure
```
.
├── code/ # Source code and scripts
│ ├── src/ # Main application logic
│ ├── tests/ # Test suites
│ ├── contracts/ # Data schema contracts
│ ├── scripts/ # Utility scripts
│ └──...
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned/processed data
│ └── logs/ # Execution logs
├── reports/ # Generated reports and plots
├── state/ # Project state and artifact hashes
└── specs/ # Research specifications
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python -m src.cli.run_pipeline`
3. Validate outputs: `python -m src.cli.validate`

## License
MIT
