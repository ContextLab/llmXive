# Quickstart Guide

## Getting Started

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd PROJ-317-the-impact-of-visual-detail-on-false-mem
 ```

2. **Install dependencies**
 ```bash
 cd code
 pip install -r requirements.txt
 ```

3. **Set up project structure**
 Run the setup script to create necessary directories:
 ```bash
 python code/setup_project_structure.py
 ```

4. **Generate ethics artifacts**
 Create ethics documentation:
 ```bash
 python code/data/ethics_generator.py
 ```

5. **Run power analysis**
 Calculate required sample size:
 ```bash
 python code/analysis/stats.py power
 ```

6. **Generate stimuli**
 Create manipulated images (mock data by default):
 ```bash
 python code/cli.py manipulate
 ```

7. **Run simulated sessions**
 Simulate participant interactions:
 ```bash
 python code/cli.py simulate --n-sessions 50
 ```

8. **Perform analysis**
 Run statistical analysis and generate visualizations:
 ```bash
 python code/cli.py analyze
 ```

## Verification

After completing the steps above, verify that the following files exist:
- `data/stimuli/manipulated/` (manipulated images)
- `data/stimuli_metadata/` (metadata YAML files)
- `data/responses/` (participant response data)
- `data/processed/power_analysis.json` (power analysis results)
- `data/processed/results/` (analysis outputs and visualizations)
- `data/ethics/informed_consent.md` (ethics documentation)

## Next Steps
- Replace mock data with real dataset if desired (see `code/config.py`).
- Customize analysis parameters in `code/config.py`.
- Run the full test suite: `pytest tests/`.

## Troubleshooting
- **Missing dependencies:** Ensure you are using Python 3.11+ and have installed all requirements.
- **Log errors:** Check `data/logs/manipulation_errors.log` for any processing failures.
- **Configuration issues:** Verify `code/config.py` settings match your environment.
