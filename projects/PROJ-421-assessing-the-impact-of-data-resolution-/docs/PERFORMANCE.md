# Performance Guide

## Overview

This document outlines performance characteristics and optimization strategies for the pipeline.

## Benchmarks

- **Runtime**: < 6 hours on a standard CPU-only runner.
- **Memory**: < 7GB RAM (via windowed I/O).
- **Disk**: ~10GB for raw and derived data.

## Optimization Strategies

### 1. Windowed I/O
- Rasters are read in chunks to avoid loading the entire file into memory.
- Adjust window size in `utils.py` for optimal performance.

### 2. Parallel Processing
- Resampling and analysis for different resolutions can be parallelized (future work).

### 3. Caching
- Intermediate results (e.g., binary maps) can be cached to avoid recomputation.

### 4. Efficient Libraries
- Use `pysal` and `numpy` for optimized spatial and numerical operations.

## Monitoring Performance

- Use `time` command to measure execution time.
- Monitor memory usage with `top` or `htop`.
- Check logs for bottlenecks.

## Scaling

- For larger datasets, consider increasing RAM or using distributed computing.
- For higher resolutions, adjust window sizes and optimize I/O.

## Future Improvements

- Implement multi-threading for independent tasks.
- Use GPU acceleration for matrix operations (if applicable).
- Optimize Gibbs Sampler implementation.
