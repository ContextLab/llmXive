# llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Overview
This project implements zero-shot drift detection for LLM interaction logs,
extending the AgentDoG 1.5 framework to identify novel attack patterns.

## Features
- Zero-shot drift scoring using semantic distance to taxonomy centroids
- Human-in-the-loop validation workflow
- Statistical validation (p-values, Cohen's d, Kappa)
- Baseline comparison with zero-shot LLM classifiers

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run setup: `python code/main.py`
3. View results in `data/processed/`

## Structure
See `plan.md` for detailed project structure.

## License
MIT
