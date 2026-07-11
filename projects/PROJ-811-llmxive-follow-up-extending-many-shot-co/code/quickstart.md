# Quickstart Guide

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: `cp.env.example.env` and edit paths.
3. Ensure `data/raw/` contains the source CoT traces.

## Running the Pipeline
1. **Parse Traces**: Run `python -m code.src.parser` (to be implemented fully in T012).
2. **Generate Prompts**: Run `python -m code.src.prompt_gen` (T022+).
3. **Inference**: Run `python -m code.src.inference` (T032).
4. **Analysis**: Run `python -m code.src.analysis` (T035).

## Validation
- Check `data/processed/validation_report.json` for T016 correlation results.
- Check `artifacts/stats_report.md` for final statistical results.
