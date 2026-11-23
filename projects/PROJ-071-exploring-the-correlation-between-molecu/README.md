# llmXive Pipeline - Memory Profiling Guide (T059)

## Overview

This document describes how to run memory profiling on the llmXive pipeline to identify
peak memory usage points, specifically during:
1. RDKit descriptor calculation (T014)
2. Dataset merging (T016a)

## Prerequisites

- Python 3.9+
- memory-profiler package installed
- All other project dependencies installed

## Installation

```bash
pip install -r requirements.txt
```

Note: `requirements.txt` includes `memory-profiler>=0.61.0` and `psutil>=5.9.0`.

## Running Memory Profiling

### Basic Usage

```bash
python code/memory_profiler.py
```

This will:
1. Run the full pipeline with memory profiling enabled
2. Profile each stage individually
3. Generate `data/memory_profile.log` with detailed memory usage statistics

### Output

The profiler generates `data/memory_profile.log` containing:
- Peak memory usage for each pipeline stage
- Total duration of profiling
- List of any errors encountered
- Detailed breakdown of memory usage by stage

Example output:
```json
{
 "pipeline_stages": {
 "ingestion": {
 "peak_memory_mb": 150.5,
 "records_processed": 1000,
 "status": "success"
 },
 "descriptors": {
 "peak_memory_mb": 320.8,
 "molecules_processed": 1000,
 "status": "success"
 }
 },
 "peak_memory_mb": 320.8,
 "total_duration_seconds": 45.2,
 "errors": []
}
```

## Interpreting Results

### Key Metrics

- **peak_memory_mb**: Highest memory usage observed during the stage
- **total_duration_seconds**: Total time taken for profiling
- **status**: Success/failure status of each stage

### Memory Hotspots

Based on profiling results:
- **Descriptor Calculation**: Typically the most memory-intensive stage
 due to RDKit molecule processing
- **Dataset Merging**: Can be memory-intensive for large datasets
- **Analysis**: Moderate memory usage for statistical computations

### Optimization Recommendations

If memory usage exceeds constraints:
1. Process data in smaller batches
2. Use streaming for large datasets
3. Optimize data types (e.g., use float32 instead of float64)
4. Clear intermediate variables explicitly

## Testing

Run the memory profiler tests:

```bash
pytest tests/test_memory_profiler.py -v
```

## Troubleshooting

### memory_profiler not installed

```bash
pip install memory-profiler psutil
```

### High Memory Usage

If memory usage exceeds available RAM:
1. Reduce dataset size for profiling
2. Use streaming mode for data loading
3. Profile individual stages separately

### Profiler Timeout

If profiling times out:
1. Increase timeout parameter in `memory_profiler.py`
2. Profile stages individually
3. Use smaller sample datasets

## Integration with Pipeline

The memory profiler can be integrated into the main pipeline:

```python
from memory_profiler import profile

@profile
def run_pipeline():
 # Pipeline code here
 pass
```

## References

- [memory-profiler documentation](https://pypi.org/project/memory-profiler/)
- T059: Memory Profiling Task
- T058: Performance Constraint Validation
