# PROJ-205: The Influence of Visual Aesthetics on Perceived Credibility

## Description
This project implements an automated scientific pipeline to study how visual design affects the perceived credibility of online information.

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set up data directories:
 ```bash
 python code/utils/setup_data_dirs.py
 ```
4. Configure IRB environment:
 ```bash
 export IRB_PROTOCOL_ID="YOUR_PROTOCOL_ID"
 python code/utils/setup_env.py
 ```

## Running the Study
Start the Streamlit survey app:
```bash
streamlit run code/survey/app.py
```

## Analysis Pipeline
Run the analysis scripts in order:
1. Preprocessing: `python code/analysis/01_preprocess.py`
2. ANOVA: `python code/analysis/01_anova.py`
3. Pairwise Tests: `python code/analysis/02_pairwise.py`
4. Report Generation: `python code/analysis/03_report.py`
5. Robustness Check: `python code/analysis/04_mixed_effects.py`

## Testing
Run the test suite:
```bash
pytest tests/
```

## License
Internal Research Use Only.
