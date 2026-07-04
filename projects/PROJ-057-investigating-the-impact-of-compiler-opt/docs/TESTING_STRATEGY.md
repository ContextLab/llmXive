# Testing Strategy

## Philosophy

The testing strategy follows the "Red-Green-Refactor" cycle. Tests are written to fail initially, ensuring that the implementation is driven by requirements.

## Test Categories

### 1. Unit Tests

**Location**: `tests/unit/`

**Scope**:
- **Configuration**: Validate flag combinations and tensor dimensions.
- **Statistics**: Verify Welch's t-test calculations and block averaging.
- **Stability**: Check L2 error and Max Diff calculations.
- **Data Generation**: Ensure deterministic output with fixed seeds.

**Examples**:
- `test_config.py`: `test_validate_flags_rejects_invalid`
- `test_stats.py`: `test_welch_ttest_significance`
- `test_stability.py`: `test_l2_norm_calculation`

### 2. Integration Tests

**Location**: `tests/integration/`

**Scope**:
- **Compilation**: Verify that kernels compile successfully with valid flags.
- **Execution**: Run a full benchmark cycle (compile, run, analyze) and verify output artifacts.
- **Stability Flow**: Compare optimized output against reference and verify error metrics.

**Examples**:
- `test_compile_run.py`: `test_compile_and_run_matmul`
- `test_stability_flow.py`: `test_compare_O3_vs_O0`
- `test_viz.py`: `test_pareto_frontier_generation`

## Running Tests

```bash
pytest tests/ -v
```

## Coverage

- **Code Coverage**: Aim for >80% coverage on core modules (`benchmarks/`, `analysis/`).
- **Edge Cases**: Test memory pressure scenarios, invalid flags, and compiler failures.

## Continuous Integration

Tests should be run automatically on every commit to ensure no regressions.

## Test Data

- **Synthetic Data**: Use `tensor_generator.py` to create deterministic test data.
- **Reference Data**: Pre-computed reference outputs are stored in `data/raw/` for integration tests.
