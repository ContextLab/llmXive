# The Influence of Chatbot Politeness on User-Perceived Quality

Research project investigating how chatbot politeness affects user-perceived quality using statistical modeling and NLP.

## Project Structure

```
.
├── code/ # Implementation scripts
│ ├── utils/ # Utility modules
│ └── *.py # Pipeline stages
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Processed data
├── tests/ # Test suite
│ ├── unit/
│ ├── integration/
│ └── contract/
├── docs/ # Documentation
├── contracts/ # Schema definitions
├── specs/ # Feature specifications
├── figures/ # Generated plots
└──.github/workflows/ # CI/CD pipelines
```

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Setup R packages (for CLMM analysis):
 ```bash
 R -e "install.packages(c('lme4', 'ordinal', 'EValue'), repos='https://cloud.r-project.org')"
 ```

## Running the Pipeline

```bash
# Verify demographics and data integrity
python code/00_verify_demographics.py

# Download and score dialogues
python code/01_download_and_score.py

# Fit CLMM model
python code/02_fit_clmm.py

# Robustness analysis
python code/03_robustness_analysis.py
```

## Testing

```bash
pytest tests/ -v
```

## License

MIT License