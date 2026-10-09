# PROJ-898: llmXive follow-up — extending "Geometric Action Model for Robot Policy Learning"

[![CI - Experimental Trial] ]()

This project extends the Geometric Action Model (GAM) by replacing its learned
neural dynamics predictor with a differentiable symbolic solver operating in the
3D latent space of a frozen Geometric Foundation Model (GFM), and evaluates
zero-shot generalization to novel object topologies (unseen kinematic chains and
deformable materials) on CPU-only hardware.

## CI

Continuous integration runs on a 2-core x86_64 GitHub Actions runner with no GPU,
enforces a 6-hour timeout (`timeout-minutes: 360`), and installs the pinned
dependencies from `requirements.txt`. The badge above asserts that the
`CI - Experimental Trial` workflow passes.

## Project structure

```text
code/ # Python modules (config, data generation, solvers, evaluation)
data/raw/ # Immutable downloaded artifacts (frozen weights, reference stats)
data/generated/ # Synthetic topology-shift test sets
data/results/ # Trial logs, statistical analyses, reports
tests/ # Unit and integration tests (pytest)
scripts/ # Thin CLI wrappers
contracts/ # Single-source-of-truth trial log schema
```

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

See `specs/001-llmxive-follow-up-extending-geometric-ac/quickstart.md` for the
full pipeline run-book (test-set generation, trial execution, statistical
analysis).

## Dependencies

All dependencies are pinned in `requirements.txt` (CPU-only; torch is installed
from the PyTorch CPU wheel index).