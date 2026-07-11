# Predicting the Impact of Alloying on Creep Resistance

This project implements an automated science pipeline to predict the impact of alloying elements on creep resistance using public data (NIMS) and thermodynamic descriptors from Materials Project.

## Project Structure

```
.
├── config/ # Configuration files (YAML)
├── contracts/ # Schema definitions for validation
├── data/ # Data storage (raw, processed, outputs)
├── docs/ # Documentation and reports
├── logs/ # Runtime logs
├── src/ # Source code
│ ├── data/ # Data acquisition and preprocessing
│ ├── models/ # Model training and evaluation
│ ├── reports/ # Report generation
│ └── utils/ # Utility functions
├── tests/ # Test suite
└── requirements.txt # Python dependencies
```

## Quickstart

1. **Setup Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

2. **Configure**
 Edit `config/settings.yaml` to set API keys (e.g., Materials Project) and paths.

3. **Run Pipeline**
 ```bash
 python src/data/pipeline.py
 ```

4. **Train Models**
 ```bash
 python src/models/main_eval.py
 ```

5. **Generate Report**
 ```bash
 python src/reports/generate_report.py
 ```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## License

MIT License
