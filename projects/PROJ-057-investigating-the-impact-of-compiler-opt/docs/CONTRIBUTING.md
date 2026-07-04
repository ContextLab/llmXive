# Contributing Guidelines

## Code Style

- **Formatting**: The project uses `black` for Python formatting. Run `black code/` before committing.
- **Linting**: `flake8` is configured in `code/.flake8`. Ensure no linting errors.
- **Type Hints**: Use type hints for all function arguments and return values.

## Testing

- **Unit Tests**: Place in `tests/unit/`. Tests should be isolated and fast.
- **Integration Tests**: Place in `tests/integration/`. Tests should verify end-to-end flows.
- **Red-Green-Refactor**: Write tests that fail initially, then implement the code to pass them.

## Adding New Kernels

1. Implement the C++ kernel in `code/kernels/<kernel_name>.cpp`.
2. Ensure the kernel accepts input tensors via command-line arguments or stdin.
3. Register the kernel in `code/benchmarks/compile_runner.py`.
4. Add corresponding analysis logic in `code/analysis/stability_check.py`.

## Adding New Optimization Flags

1. Update the flag list in `code/benchmarks/config.py`.
2. Ensure the flag is compatible with the C++ standard (C++17).
3. Update documentation in `docs/CONFIGURATION.md`.

## Reporting Issues

When reporting issues, include:
- Compiler version (`g++ --version`)
- Python version
- Full error traceback
- Configuration used (flags, dimensions)

## Commit Messages

Use the following format:
`[TASK-ID] [TYPE] Short description`

Example:
`[T035] [DOCS] Update architecture documentation`
