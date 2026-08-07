# Documentation Index

This directory contains the final reports and documentation for the PROJ-735 study.

## Reports

- **benchmark_report.md**: Detailed analysis of DFT-D3 performance against CCSD(T)/CBS references, including scaling factor derivation and statistical significance.
- **correlation_report.md**: Analysis of the relationship between dispersion terms and bulk properties (density, viscosity).
- **review_response.md**: Formal response to reviewer comments from Linus Pauling-simulated and Marie Curie-simulated.

## Usage

These reports are generated automatically by the pipeline scripts in `code/`.
To regenerate the reports, run:

```bash
python code/generate_reports.py
```

Ensure that the input data files (`data/raw_energies.csv`, `data/scaling_results.json`, `data/correlation_results.json`) exist before running the script.
