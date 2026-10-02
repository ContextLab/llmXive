# llmXive Research Pipeline: The Impact of Simulated Social Validation

This project implements an automated research pipeline to analyze the impact of simulated social validation on self-perception in adolescents.

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical modeling and analysis
│ ├── data/ # Data loading, generation, and processing
│ ├── utils/ # Utilities, constants, and exceptions
│ ├── viz/ # Visualization generation
│ └── main.py # Main orchestration script
├── data/
│ ├── raw/ # Raw data files
│ └── processed/ # Processed data and outputs
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

Run the main pipeline:
```bash
cd code
python main.py
```

## Key Features

- **Data Acquisition**: Attempts to load real data; falls back to synthetic SEM-based generation.
- **Statistical Modeling**: Multiple linear regression with confounder adjustment and VIF checks.
- **Robustness Checks**: Sensitivity analysis across outlier strategies and confounder states.
- **Visualization**: Diagnostic plots (scatter, residuals).
- **Causal Language Guard**: Automatically rejects reports containing causal language.

## License

MIT License
