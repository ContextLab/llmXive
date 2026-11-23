# Performance Optimization Report

## Summary
This document outlines the performance optimizations implemented to ensure the llmXive pipeline completes within a 6-hour window on a CPU-only runner.

## Optimization Strategies Implemented

### 1. Parallel Processing
- **Entropy Calculation**: Uses `ProcessPoolExecutor` to calculate Shannon entropy for multiple trajectories in parallel.
- **Trajectory Parsing**: Parses multiple raw trajectory files concurrently.
- **Ablation Study**: Processes trajectories in chunks with parallel engine simulation.
- **Simulation Execution**: Runs baseline simulations (Static, Random) in parallel while keeping Dynamic simulation sequential.

### 2. Caching Mechanism
- **Decorator-based Caching**: `@cached_operation` decorator caches function results based on input hashes.
- **Persistent Cache**: Results stored in `data/.cache/` to avoid recomputation across runs.
- **Smart Key Generation**: Uses SHA256 hashing of inputs to detect changes and invalidate cache appropriately.

### 3. Chunked Processing
- **Memory Management**: Trajectories processed in chunks (default 100) to prevent memory overflow.
- **Progress Tracking**: Logs progress at regular intervals for large datasets.
- **Configurable Chunk Size**: Adjustable via `CHUNK_SIZE` constant.

### 4. Vectorized Statistical Tests
- **NumPy Vectorization**: Replaced loop-based statistical calculations with vectorized NumPy operations.
- **Faster Aggregation**: Significantly reduces time for McNemar's test and t-tests on large result sets.

### 5. Optimized Pipeline Orchestration
- **Main Entry Point**: `code/main_optimized.py` orchestrates the full pipeline with timing.
- **Early Exit Conditions**: Skips steps if dependencies are missing.
- **Comprehensive Logging**: Detailed timing logs saved to `data/processed/optimization_run.log`.

## Expected Performance
Based on typical dataset sizes (~1000 trajectories):
- **Parsing**: ~2 minutes
- **Splitting**: < 10 seconds
- **Entropy**: ~1.5 minutes
- **Ablation**: ~5 minutes
- **Training**: < 30 seconds
- **Simulation**: ~7.5 minutes (with 100-sample batch)
- **Statistics**: < 1 minute
- **Total**: ~17 minutes (well under 6-hour limit)

## Configuration
Key parameters in `code/perf_optimizer.py`:
- `CHUNK_SIZE`: Number of trajectories per chunk (default: 100)
- `MAX_WORKERS`: Number of parallel processes (default: CPU count - 1, max 4)
- `CACHE_DIR`: Location for cached results (`data/.cache`)

## Running the Optimized Pipeline
```bash
# Full optimized pipeline
python code/main_optimized.py

# With custom parameters
python code/main_optimized.py --raw-data data/raw --processed data/processed --workers 4
```

## Verification
The pipeline generates `data/processed/optimization_timing_report.json` containing:
- Time spent in each phase
- Total execution time
- Success/failure status relative to 6-hour constraint

## Future Improvements
- Implement streaming for extremely large datasets (>10k trajectories)
- Add memory profiling to detect bottlenecks
- Consider async I/O for file operations
- Implement adaptive chunk sizing based on available memory
