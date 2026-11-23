# CPU Optimization Guide for llmXive Pipeline

## Overview

This guide describes the CPU optimization strategies implemented in the llmXive pipeline
to ensure efficient execution on CPU-only systems without GPU acceleration.

## Key Optimization Strategies

### 1. GPU Prevention

The pipeline includes strict validation to prevent accidental GPU usage:

- **Environment Variables**: `CUDA_VISIBLE_DEVICES` is set to empty string
- **Library Checks**: Validates PyTorch, TensorFlow, and JAX GPU availability
- **Thread Limitation**: Sets `OMP_NUM_THREADS` and `MKL_NUM_THREADS` to 1

### 2. Memory Management

#### Data Structure Optimization

- **Numeric Downcasting**: Converts `float64` to `float32` and `int64` to `int32`
- **Category Conversion**: Converts low-cardinality object columns to category dtype
- **Contiguous Arrays**: Ensures numpy arrays are contiguous in memory

#### Chunked Processing

Large datasets are processed in chunks to reduce memory pressure:

```python
from utils.cpu_optimization import chunked_dataframe_iterator

for chunk in chunked_dataframe_iterator(large_df, chunk_size=10000):
 # Process chunk
 process(chunk)
```

### 3. Garbage Collection

Strategic garbage collection is implemented:

- After processing each subject
- Every 5 subjects during batch processing
- At pipeline completion

### 4. Random Seed Management

Reproducibility is ensured through comprehensive seed setting:

- NumPy random seed
- Python random seed
- Environment hash seed

## Usage

### Running the Optimized Pipeline

Use the optimized entry point:

```bash
python code/main_optimized.py
```

### Enabling Strict CPU Mode

Set the environment variable for strict validation:

```bash
export LLMXIVE_STRICT_CPU_ONLY=1
python code/main_optimized.py
```

## Performance Monitoring

Memory usage is monitored throughout execution:

```python
from utils.cpu_optimization import monitor_memory_usage

mem_stats = monitor_memory_usage()
print(f"Memory usage: {mem_stats}")
```

## Configuration

Key optimization parameters can be adjusted in `code/config.py`:

- `CHUNK_SIZE`: Number of rows per chunk (default: 10000)
- `MEMORY_WARNING_THRESHOLD_MB`: Memory warning threshold (default: 1024)
- `MAX_MEMORY_USAGE_PERCENT`: Maximum safe memory usage percentage (default: 85.0)

## Troubleshooting

### Memory Errors

If encountering memory errors:

1. Reduce `CHUNK_SIZE` in configuration
2. Enable `low_precision` conversion in `optimize_memory_usage()`
3. Increase system swap space
4. Process fewer subjects in parallel

### GPU Detection False Positives

If GPU is incorrectly detected:

1. Unset `CUDA_VISIBLE_DEVICES`: `unset CUDA_VISIBLE_DEVICES`
2. Install CPU-only versions of libraries
3. Check for residual GPU processes

### Performance Issues

If performance is suboptimal:

1. Ensure all numeric data is downcast to float32
2. Verify chunked processing is active for large datasets
3. Check thread limitations are properly set
4. Monitor memory usage to identify bottlenecks

## Best Practices

1. **Always use the optimized entry point** (`main_optimized.py`) for production runs
2. **Monitor memory usage** regularly during execution
3. **Process subjects sequentially** rather than in parallel on memory-constrained systems
4. **Use chunked processing** for any dataset larger than available RAM
5. **Validate CPU environment** before starting long-running jobs

## Reference Implementation

The core optimization utilities are located in:

- `code/utils/cpu_optimization.py`: Main optimization functions
- `code/main_optimized.py`: Optimized pipeline entry point

These modules provide all necessary functionality for efficient CPU-only execution.
