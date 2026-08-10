# Analysis Module

This directory contains scripts for analyzing training results and evaluating model performance.

## Scripts

- `statistical_test.py`: Runs Mixed-Model Repeated-Measures ANOVA on Generalization Gap curves.
- `evaluate_human_eval.py`: Runs HumanEval benchmark suite on final checkpoints.
- `compute_metrics.py`: Calculates Pearson correlation between gap slope and HumanEval scores.
- `evaluate_wikitext2.py`: Performs cross-domain validation on WikiText-2.
- `power_analysis.py`: Performs a priori power analysis for the experiment regime.
- `report_generator.py`: Generates final statistical reports and analysis summaries.

## Usage

These scripts are typically invoked by `main.py` or run independently after training completes.
They expect training logs and model checkpoints to be available in the `data/artifacts/` directory.