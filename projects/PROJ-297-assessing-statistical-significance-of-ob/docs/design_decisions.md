# Design Decisions

This document records significant design decisions made during the development of the Statistical Significance Assessment Pipeline.

## Architecture Decisions

### ADR-001: Modular Pipeline Architecture

**Status:** Accepted
**Date:** 2024-01-15

**Context:**
The project requires a flexible, testable, and maintainable architecture that can handle multiple statistical analyses across various datasets.

**Decision:**
Implement a modular architecture with clear separation of concerns:
- `loaders.py`: Data ingestion and hygiene
- `stats_engine.py`: Statistical computations
- `correction.py`: Multiple testing correction
- `viz.py`: Visualization generation
- `main.py`: Pipeline orchestration

**Consequences:**
- Each module can be tested independently
- Easy to swap out components (e.g., different correction methods)
- Clear API boundaries between modules
- Slightly more complex import structure

### ADR-002: Configuration Management

**Status:** Accepted
**Date:** 2024-01-15

**Context:**
The pipeline needs configurable parameters (thresholds, permutation counts, paths) that may vary between runs.

**Decision:**
Use a centralized configuration module (`code/config.py`) with:
- Path management via `get_config()` and `ensure_dirs()`
- Default values with override capability
- No hardcoded dataset lists (dynamic discovery)

**Consequences:**
- Consistent configuration across modules
- Easy to change defaults without code modification
- Central location for project settings
- Must ensure config is loaded before pipeline execution

## Statistical Method Decisions

### ADR-010: Permutation Count Selection

**Status:** Accepted
**Date:** 2024-01-20

**Context:**
The specification mentioned N=2,000 permutations, but practical constraints (CPU-only CI, 6-hour runtime limit) require optimization.

**Decision:**
Use N=1,000 permutations as the default, with a reduced N=500 for clustering coefficient on datasets with >50 variables.

**Rationale:**
- N=1,000 provides sufficient precision for p-value estimation
- Meets the "sufficient number" requirement from the specification
- Aligns with Plan Phase 1 feasibility constraints
- Reduced count for clustering coefficient prevents excessive runtime

**Consequences:**
- P-value resolution of approximately 0.001
- Runtime within 6-hour limit for most datasets
- Must document the optimization in reports

### ADR-011: Benjamini-Yekutieli vs Benjamini-Hochberg

**Status:** Accepted
**Date:** 2024-01-22

**Context:**
Multiple testing correction is required for FDR control. The choice between BH and BY procedures depends on dependence assumptions.

**Decision:**
Use Benjamini-Yekutieli (BY) procedure for all significance testing.

**Rationale:**
- Correlation tests exhibit arbitrary dependence
- BY procedure controls FDR under any dependence structure
- Specification explicitly requires BY (FR-004)
- More conservative than BH but statistically rigorous

**Consequences:**
- Slightly more conservative significance thresholds
- Requires Constitution Amendment ratification (T020)
- Must document BY usage in all reports

### ADR-012: Empirical P-Value Formula

**Status:** Accepted
**Date:** 2024-01-22

**Context:**
Empirical p-values from permutation testing can be 0 or 1, which causes issues in downstream analysis.

**Decision:**
Use the formula (r+1)/(N+1) for empirical p-value calculation.

**Rationale:**
- Avoids p-value of 0 or 1
- Provides unbiased estimation
- Standard practice in permutation testing
- Implemented in `calculate_empirical_p_value()`

**Consequences:**
- Minimum p-value is 1/(N+1)
- Maximum p-value is N/(N+1)
- Consistent with statistical literature

## Data Handling Decisions

### ADR-020: Dynamic Dataset Discovery

**Status:** Accepted
**Date:** 2024-01-18

**Context:**
Hardcoding dataset lists is fragile and doesn't scale. The pipeline needs to discover valid datasets dynamically.

**Decision:**
Implement dynamic discovery mechanism:
1. Query UCI repository for multivariate datasets
2. Filter for >=20 continuous variables
3. Apply hygiene pipeline
4. Ensure >=3 valid datasets

**Consequences:**
- More robust to UCI repository changes
- Always uses current datasets
- Requires network access
- May fail if UCI is unreachable (fails loudly)

### ADR-021: Data Hygiene Pipeline

**Status:** Accepted
**Date:** 2024-01-18

**Context:**
Real-world datasets have missing values, constant variables, and mixed types that must be handled.

**Decision:**
Implement strict hygiene pipeline:
1. Drop rows with any missing values
2. Detect and exclude constant variables
3. Filter to continuous variables only
4. Validate minimum variable count (20)

**Consequences:**
- Ensures clean input for statistical analysis
- May reduce dataset size significantly
- Must be applied consistently across all datasets
- No silent fallback to synthetic data

### ADR-022: Spearman Correlation Handling

**Status:** Accepted
**Date:** 2024-01-25

**Context:**
Spearman correlation is useful for exploratory analysis but may not be appropriate for primary significance testing.

**Decision:**
- Compute both Pearson and Spearman matrices
- Use Pearson for primary analysis (graph construction, significance testing)
- Store Spearman matrices in `output/exploratory/`
- Exclude Spearman from BY correction and primary reporting

**Consequences:**
- Provides exploratory insights without compromising primary analysis
- Clear separation between primary and exploratory results
- Spearman matrices available for comparison

## Visualization Decisions

### ADR-030: Primary Threshold Selection

**Status:** Accepted
**Date:** 2024-01-28

**Context:**
Multiple thresholds are tested, but a primary threshold is needed for main visualizations.

**Decision:**
Use |r| > 0.3 as the primary threshold for visualizations.

**Rationale:**
- Balances sparsity and density in network graphs
- Common threshold in correlation network literature
- Provides clear signal-to-noise ratio
- Specified in T025b

**Consequences:**
- Primary visualizations always use 0.3 threshold
- Other thresholds available in sensitivity analysis
- Consistent with field conventions

### ADR-031: Sensitivity Threshold Sweep

**Status:** Accepted
**Date:** 2024-01-28

**Context:**
Threshold sensitivity analysis requires a range of thresholds to test.

**Decision:**
Test thresholds: {0.1, 0.2, 0.3, 0.4, 0.5}

**Rationale:**
- Covers low to high correlation thresholds
- Includes 0.1 baseline (specification requirement)
- Evenly spaced for clear trend visualization
- Explicitly cites FR-005

**Consequences:**
- 5 separate analyses per dataset
- Clear sensitivity profile across thresholds
- 0.1 threshold always included in reports

## Performance Decisions

### ADR-040: Runtime Optimization for Clustering Coefficient

**Status:** Accepted
**Date:** 2024-02-01

**Context:**
Clustering coefficient calculation is computationally expensive on large graphs.

**Decision:**
Reduce N to 500 for clustering coefficient when variable count > 50.

**Rationale:**
- Prevents excessive runtime on large datasets
- Authorized by Plan Phase 1 exception
- Clustering coefficient less sensitive to N than other statistics
- Ensures pipeline completes within 6-hour limit

**Consequences:**
- Different N for different statistics
- Must track N used for each statistic
- Documented in results for reproducibility

### ADR-041: Memory Management

**Status:** Accepted
**Date:** 2024-02-01

**Context:**
Large datasets and many permutations can exceed available memory.

**Decision:**
- Process datasets sequentially (not in parallel)
- Stream permutation results where possible
- Clear intermediate results between datasets
- Fail loudly if memory issues occur

**Consequences:**
- Slower but more reliable execution
- Works within CI memory constraints
- No silent failures or data loss

## Error Handling Decisions

### ADR-050: Fail-Loudly Policy

**Status:** Accepted
**Date:** 2024-01-16

**Context:**
Silent failures can lead to incorrect results being accepted.

**Decision:**
Implement fail-loudly policy:
- No synthetic fallback when real data fetch fails
- Raise explicit exceptions (FileNotFoundError, ValueError)
- Clear error messages with actionable information
- No placeholder data or results

**Consequences:**
- Runs fail visibly when data is unavailable
- Easier to diagnose and fix issues
- Prevents fabrication of results
- Complies with Constitution VII

### ADR-051: Data Integrity Verification

**Status:** Accepted
**Date:** 2024-01-16

**Context:**
Downloaded data must be verified for integrity.

**Decision:**
- Implement checksumming where UCI provides checksums
- Store SHA256 hashes in `data/raw/checksums.json`
- Verify hashes on subsequent runs
- Fail if checksum mismatch detected

**Consequences:**
- Ensures reproducibility
- Detects corrupted downloads
- Adds overhead to download process
- Complies with Constitution I

## Future Considerations

### ADR-100: Potential Parallel Processing

**Status:** Deferred
**Date:** 2024-02-05

**Context:**
Current implementation processes datasets sequentially.

**Decision:**
Defer parallel processing until:
- Memory constraints are better understood
- CI infrastructure supports parallel execution
- Thread safety is verified

**Consequences:**
- Current sequential approach is safer
- Parallel processing may be added in future
- Architecture allows for future parallelization

### ADR-101: Additional Statistical Tests

**Status:** Deferred
**Date:** 2024-02-05

**Context:**
Current implementation tests 4 network statistics.

**Decision:**
Defer additional statistics until:
- Current statistics are fully validated
- Clear need for additional metrics is established
- Performance impact is understood

**Consequences:**
- Focused implementation on core statistics
- Easy to add new statistics following existing pattern
- Architecture supports extension
