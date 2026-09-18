# Performance Optimization

## Chunked Processing
For datasets larger than 7GB, the pipeline uses chunked processing to avoid memory overflow.

## Implementation
- `code/data/chunked_processor.py`: Handles chunked data loading and processing.
- `code/models/lmm_chunked.py`: Handles chunked LMM analysis.

## Configuration
Chunk size can be configured in `code/config.py`.

## Benchmarks
- **1GB Dataset**: Processed in < 5 minutes.
- **7GB Dataset**: Processed in < 30 minutes (depending on hardware).

## Optimization Tips
- Use `streaming=True` for large datasets to avoid loading everything into memory.
- Monitor memory usage during processing.
- Use alternative optimizers for faster convergence in LMM.
