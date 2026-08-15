# llmXive Research Pipeline: Investigating the Relationship Between Brain Network Dynamics and VR Therapy Response

## Project Overview
This project implements an automated scientific pipeline to investigate the relationship between brain network dynamics (functional connectivity, modularity, efficiency) and response to VR-based therapy for anxiety disorders. The pipeline processes resting-state fMRI data, computes network metrics, and performs statistical analysis to identify associations.

## Quickstart
See `docs/quickstart.md` for detailed execution instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (N=10 subset for CI)
python code/main.py --stage download
python code/main.py --stage validate
python code/main.py --stage preprocess
python code/main.py --stage compute
python code/main.py --stage analyze
python code/main.py --stage report
```

## Known Limitations

### 1. Underpowered Hypothesis Testing (SC-004)
The pipeline includes a mandatory power analysis (Task T031) using `statsmodels.stats.power.FTestPower`.
- **HALT Condition**: If the number of subjects (N) is less than 5, the pipeline halts immediately with the error: "Insufficient Power: N < 5".
- **Exploratory Mode**: If 5 ≤ N < `min_N_required` (calculated for power=0.8, alpha=0.05, effect_size=0.15), the pipeline does not halt but flags a warning: "WARNING: Underpowered for hypothesis testing (Power < 0.8)". In this mode, the analysis switches to **Exploratory Mode**, reporting effect sizes and confidence intervals but **without claiming statistical significance** via p-values.
- **Minimum N**: The calculated `min_N_required` is saved to `data/metrics/power_analysis.json` and explicitly referenced in `reports/results.md`. Users should verify this value against their actual sample size before interpreting results.

### 2. Associational Framing Constraint (FR-008, SC-005)
The final report (`reports/results.md`) strictly enforces an "Associational" framing unless the input metadata explicitly confirms a randomized design.
- **Logic**: The pipeline checks `metadata.study_design` for the string 'randomized' OR `metadata.randomized` for the boolean `true`.
- **Default Behavior**: If these fields are missing, null, or do not match the criteria above, the report **must** state: "Findings are framed as ASSOCIATIONAL."
- **Implication**: Even if a positive association is found, the results cannot be interpreted as causal evidence of VR therapy efficacy without verified randomized controlled trial metadata. This constraint prevents over-interpretation of observational data.

### 3. Data Availability
The pipeline relies on a verified public dataset containing paired pre/post fMRI scans and validated anxiety scores (GAD-7, HAM-A). If no such dataset is found during the multi-source aggregation phase (T001a), the pipeline halts with a fatal error: "BLOCKED: No verified dataset source found after multi-source aggregation. Project cannot proceed."

### 4. Computational Constraints
The pipeline is optimized for CPU execution (2 cores, 7GB RAM) and is designed to process a subset of N=10 subjects within 6 hours. Large-scale processing requires scaling up resources or adjusting the subset size in `code/config.py`.

### 5. Collinearity Handling
If Variance Inflation Factor (VIF) > 5 is detected among network metrics, the pipeline automatically switches to Principal Component Analysis (PCA) to resolve collinearity. If PCA fails to reduce the dimensionality effectively (fewer than 2 components explaining >90% variance), the pipeline halts with "Collinearity Unresolvable". Ridge regression is explicitly forbidden per FR-005.

## Directory Structure
- `code/`: Source code for the pipeline
- `data/raw/`: Downloaded raw data
- `data/processed/`: Preprocessed NIfTI files
- `data/metrics/`: QC metrics, network metrics, and statistical results
- `reports/`: Final analysis reports and sensitivity analysis
- `logs/`: Execution logs
- `tests/`: Unit and integration tests

## Dependencies
See `requirements.txt` for the full list of dependencies, including `nilearn`, `networkx`, `bctpy`, `statsmodels`, and `scikit-learn`.

## License
[Insert License Here]