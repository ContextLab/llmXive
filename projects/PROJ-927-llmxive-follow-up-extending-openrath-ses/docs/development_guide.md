# Development Guide

## Architecture Principles

1. **Single Source of Truth**: All metrics and corruption status must be stored in central JSON files (`aggregated_metrics.json`, `corruption_map.json`).
2. **Immutability**: Ground truth files must never be modified after generation.
3. **Determinism**: All random processes must be seeded.
4. **Fail Loudly**: Do not use synthetic fallbacks for real data. If a fetch fails, raise an error.

## Module Responsibilities

- **Generators**: Create deterministic workflows and ground truth.
- **Executors**: Run workflows through specific architectures (Event-Log vs. Session-First).
- **Simulators**: Inject corruption and jitter.
- **Reconstructors**: Rebuild state from corrupted logs.
- **Analyzers**: Calculate metrics and perform statistical tests.
- **Utils**: Handle checksums and file operations.

## Adding New Features

1. **Define Task**: Add a new task to `tasks.md` with a clear description and file paths.
2. **Update Schema**: If new data structures are introduced, update `code/generators/schemas.py` or `code/simulators/schemas.py`.
3. **Implement**: Write the code in the designated module.
4. **Test**: Write unit tests in `tests/unit/`.
5. **Document**: Update `README.md` and `docs/` as needed.

## Debugging

- **Logs**: Check `logging` output for detailed execution traces.
- **State**: Inspect `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml` for checkpoint and hash information.
- **Data**: Verify files in `data/processed/` for intermediate results.

## Performance Optimization

- Use `streaming=True` for large datasets.
- Implement batched processing in `code/main.py`.
- Monitor memory usage with `tests/bench_sweep.py`.
