# Bayesian Hierarchical Modeling of Misinformation Cascade Size

This project develops Bayesian hierarchical models to quantify how network
topology and user-susceptibility features predict the size of misinformation
cascades on online social networks.

## Project Structure

```text
code/ # Pipeline source code (pipeline, feature engineering, models)
data/ # Raw and processed cascade data (JSON edge-list format)
results/ # Pipeline outputs (features, traces, posterior summaries)
tests/ # Contract and integration tests
contracts/ # JSON schemas for input/output validation
docs/ # Additional documentation
```

## Quick Start

See `quickstart.md` for full step-by-step instructions. In brief:

```bash
bash code/pipeline/run_pipeline.sh --data data/raw/ --out results/
```

## Model Specification

Model priors, hyper-parameters, and random-effect structure are defined in
`code/models/model_spec.yaml` (see the model specification transparency
requirement).

## License

TBD
