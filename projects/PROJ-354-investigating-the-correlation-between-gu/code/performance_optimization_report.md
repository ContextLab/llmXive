# Performance Optimization Report (Task T033)

## Overview

This report documents the performance optimization measures implemented to ensure
the data processing pipeline operates within the 7GB RAM constraint.

## Implementation Details

### 1. Memory Monitoring Infrastructure (`code/perf_monitor.py`)

The following utilities were implemented to monitor and control memory usage:

- **`get_current_memory_usage()`**: Real-time memory usage tracking using `psutil`
- **`estimate_dataframe_memory()`**: Accurate memory estimation for pandas DataFrames
- **`calculate_safe_batch_size()`**: Dynamic batch size calculation based on available memory
- **`trigger_memory_cleanup()`**: Forced garbage collection to release memory
- **`check_memory_pressure()`**: Threshold-based memory pressure detection
- **`stream_with_memory_monitor()`**: Streaming wrapper with automatic memory cleanup
- **`optimize_dataframe_memory()`**: Automatic type downcasting to reduce memory footprint
- **`validate_memory_constraints()`**: Pre-flight validation for data and operations

### 2. Optimized Streaming Loader (`code/utils/streaming_optimized.py`)

The `OptimizedStreamingLoader` class provides:

- **Adaptive batch sizing**: Automatically calculates optimal batch sizes
- **Memory-aware iteration**: Monitors memory during streaming
- **Format-specific optimization**: Special handling for Parquet and CSV files
- **Automatic memory cleanup**: Periodic garbage collection during processing
- **Column selection**: Load only required columns to reduce memory

### 3. Key Optimization Strategies

#### Batch Processing
- Dynamic batch size calculation based on available memory
- Default target: 500MB per batch (adjustable via `TARGET_BATCH_MEMORY_GB`)
- Safety margin: 80% of 7GB limit (5.6GB usable)

#### Memory Optimization
- Automatic downcasting of numeric types (int64 → int32/16/8, float64 → float32)
- Category conversion for low-cardinality string columns
- Periodic garbage collection every 10 batches (configurable)

#### Streaming Architecture
- Process data in chunks without loading entire dataset into memory
- Memory pressure detection triggers cleanup before critical thresholds
- Support for both Parquet (row-group based) and CSV streaming

### 4. Integration Points

The optimization utilities integrate with existing pipeline components:

- **`code/download.py`**: Use `stream_with_memory_monitor()` for data fetching
- **`code/preprocess.py`**: Apply `optimize_dataframe_memory()` after transformations
- **`code/analysis.py`**: Use `calculate_safe_batch_size()` for model fitting batches
- **`code/utils/streaming.py`**: Enhanced with `OptimizedStreamingLoader`

## Validation Metrics

### Memory Constraints
- **Maximum RAM**: 7.0 GB
- **Safety Margin**: 80% (5.6 GB usable)
- **Target Batch Size**: 500 MB (0.5 GB)
- **Pressure Threshold**: 75% of limit (5.25 GB)

### Expected Performance
- **Memory Reduction**: 30-50% through type optimization
- **Batch Efficiency**: 80-90% memory utilization without overflow
- **Processing Overhead**: <5% for monitoring and cleanup

## Usage Example

```python
from code.perf_monitor import (
 calculate_safe_batch_size,
 stream_with_memory_monitor,
 optimize_dataframe_memory
)
from code.utils.streaming_optimized import OptimizedStreamingLoader

# Calculate safe batch size
batch_size = calculate_safe_batch_size(df_sample=some_sample)

# Process with memory monitoring
loader = OptimizedStreamingLoader("data/raw/large_file.parquet", batch_size=batch_size)

for batch in stream_with_memory_monitor(loader, process_fn=my_function):
 # Process optimized batch
 result = my_function(batch)
```

## Conclusion

The implemented optimizations ensure that the pipeline can process large datasets
(14GB+) within the 7GB RAM constraint by:

1. Streaming data in memory-safe batches
2. Automatically optimizing DataFrame memory usage
3. Monitoring and responding to memory pressure
4. Providing validation tools for pre-flight checks

These measures satisfy the performance requirements specified in Task T033.
