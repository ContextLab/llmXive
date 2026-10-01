# Evaluating the Robustness of Common Statistical Tests to Non-Independence

## Summary
This project investigates how violations of the independence assumption affect the Type I error rates and statistical power of t-tests, ANOVA, and Chi-squared tests. Using a rigorous Monte Carlo simulation framework, we inject controlled dependencies (temporal, spatial, hierarchical) into real public datasets and synthetic data to quantify these effects.

## Quick Start

### Prerequisites
- Python 3.11+
- `pip`

### Installation
```bash
git clone <repository-url>
cd PROJ-483-evaluating-the-robustness-of-common-stat
pip install -r requirements.txt
```

### Running the Pipeline
Execute the full simulation sweep:
```bash
python code/main.py
```

### Outputs
- `results/aggregated_unified.csv`: Raw simulation data.
- `results/type1_error_table.md`: Summary table of Type I error inflation.
- `figures/`: Visualizations of error rate curves and power analysis.

## Documentation
- [Scientific Methodology](docs/scientific_methodology.md)
- [Binning Strategy for Chi-Squared](docs/binning_strategy.md)
- [API Reference](docs/README.md)

## Key Features
- **Real Data Only**: Uses verified UCI datasets (Wine, Car, Zoo). [UNRESOLVED-CLAIM: c_f861e05b — status=not_enough_info]
- **Fail-Loud Policy**: Pipeline halts on data fetch errors; no synthetic fallback.
- **Dual Paradigms**: "Generate-then-Inject" for synthetic, "Inject-then-Permute" for real data.
- **Robust Metrics**: Clopper-Pearson confidence intervals and Mann-Kendall trend tests.

## Performance
Optimized for CPU-only runners (2-core, 7GB RAM). Target: 10,000 replications in < 6 hours. [UNRESOLVED-CLAIM: c_04d72011 — status=refuted]

## License
[Insert License]