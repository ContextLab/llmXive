# Performance Benchmarks

## Resource Constraints

The pipeline is optimized to run within the following constraints:
- **Memory**: < 6 GB RSS (Peak).
- **Time**: < 6 hours (Wall-clock).
- **CPU**: Single-threaded or limited multi-threading (no GPU).

## Benchmark Results

### Ingestion (T009)
- **LAGEOS-1 (1 Year)**: ~2.5 GB raw data.
- **Fetch Time**: ~15 minutes (network dependent).
- **Parsing Time**: ~5 minutes.

### Preprocessing (T016-T019)
- **Filtering**: < 1 minute for 1M rows.
- **Alignment**: < 2 minutes.

### Orbit Determination (T024a)
- **Separate Fit**: ~10-20 minutes per satellite (depending on arc length).
- **Convergence**: Typically < 15 iterations.

### Analysis & Validation (T026-T037)
- **Sensitivity Sweep**: ~5 minutes for 3 geopotential models.
- **Report Generation**: < 1 minute.

### Total Pipeline Runtime
- **Estimated**: ~45-60 minutes for a 1-year dataset on standard hardware.
- **Memory Peak**: ~3.2 GB during the estimation phase.

## Optimization Notes

- **Vectorization**: `code/data/preprocessing.py` uses NumPy vectorization for filtering.
- **Caching**: Intermediate results (e.g., force model lookups) are cached where possible.
- **Streaming**: Large datasets are processed in chunks to avoid memory spikes.

## Known Bottlenecks

- **Geopotential Calculation**: The GGM model evaluation is the most computationally expensive step. Future optimization could involve pre-computed grids or reduced-order models.
- **ILRS API**: Rate limiting on the ILRS server can impact ingestion time. Retry logic (T009) handles this gracefully.
