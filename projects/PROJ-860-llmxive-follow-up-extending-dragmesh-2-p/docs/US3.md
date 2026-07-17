# User Story 3: CPU-Tractable Inference Pipeline

## Goal

Ensure the entire experiment (data gen, training, eval, analysis) runs within
6 hours and 7GB RAM on a CPU-only runner.

## Acceptance Criteria

- [ ] No CUDA usage (enforced via environment checks)
- [ ] Peak memory usage ≤ 7GB
- [ ] Wall-clock time ≤ 6 hours
- [ ] Memory profiling integrated
- [ ] CI workflow enforces constraints
- [ ] Full benchmark runs successfully

## Implementation Details

### Memory Optimization
- Tracemalloc profiling for peak memory tracking
- Batch size optimization
- Simulation step optimization
- Streaming data loading where applicable

### CPU Enforcement
- Explicit CUDA checks in environment setup
- PyBullet CPU-only configuration
- No GPU-dependent libraries

### CI Integration
- GitHub Actions workflow with timeout
- Memory profiling in CI
- Automated constraint verification

## Test Cases

### Unit Tests
- Memory profiling script functionality
- CUDA enforcement checks

### Integration Tests
- Full pipeline benchmark execution
- CI workflow validation

## Files

- `code/environment.py`: CPU-only enforcement
- `code/memory_profiler.py`: Memory profiling utilities
- `code/benchmark_runner.py`: End-to-end benchmark
- `.github/workflows/test-cpu-pipeline.yml`: CI configuration

## Dependencies

- All US1 and US2 components
- T004: CPU-only environment setup

## Success Metrics

- **Memory**: Peak usage ≤ 7GB (measured via tracemalloc)
- **Time**: Wall-clock ≤ 6 hours (measured via benchmark_runner)
- **Hardware**: 0% CUDA usage (verified via environment checks)
