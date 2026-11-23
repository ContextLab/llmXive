# llmXive: Dynamic Socio-Cognitive State Injection

An automated science pipeline for researching the impact of dynamic socio-cognitive state injection on LLM-mediated conflict resolution.

## Features

- **Synthetic Trajectory Generation**: Creates conflict dialogues with targeted oversampling of high emotional reactivity and diverse cultural identity.
- **Dynamic State Injection**: Runs experiments comparing "Static" baseline prompts vs. "Dynamic" adapter injections.
- **Consensus Gap Analysis**: Computes statistical significance of gap closure between conditions.
- **CPU-Only Execution**: Designed for reproducibility on standard hardware without GPU dependencies.

## Project Structure

```
.
├── code/
│ ├── analysis/ # Metrics, stats, validation
│ ├── data/ # Generators, loaders
│ ├── experiments/ # Runner, prompts, retry logic
│ ├── models/ # Classifier, evaluator, entities
│ ├── config.py # Configuration and logging
│ └── setup_structure.py
├── data/
│ ├── raw/
│ ├── processed/ # Generated trajectories, logs
│ └── results/ # Reports, stats
├── tests/ # Unit and integration tests
├── specs/ # Design documents
└── requirements.txt
```

## Quickstart

See `specs/001-dynamic-state-injection/quickstart.md` for detailed execution steps.

## Validation

Run the end-to-end validation:
```bash
python -m code.analysis.quickstart_validator
```

## License

[License Information]
