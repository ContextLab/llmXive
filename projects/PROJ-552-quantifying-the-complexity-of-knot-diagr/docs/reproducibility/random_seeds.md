# Random Seed Values Documentation

## Overview

This document records all random seed values used throughout the knot complexity analysis pipeline to ensure reproducibility of stochastic operations per FR-007 and Constitution Principle I.

## Seed Values

### Primary Random Seed

| Module | Operation | Seed Value | Purpose |
|--------|-----------|------------|---------|
| `code/analysis/regression.py` | Bootstrap sampling for confidence intervals | `42` | Statistical resampling for regression model validation |
| `code/analysis/precision.py` | Random subsampling for precision estimation | `123` | Precision validation across knot subsets |
| `code/analysis/exploratory.py` | Random knot selection for visualization examples | `456` | Representative sample selection for scatter plots |

### Configuration

All random seeds are set at the module level using the following pattern:

```python
import numpy as np
import random

# Set seeds at module initialization
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
```

## Verification

Per T007 (random seed pinning implementation), all stochastic operations in the codebase have been verified to use pinned seeds. The following verification checklist confirms compliance:

- [x] `code/analysis/regression.py` - All random operations use seed `42`
- [x] `code/analysis/precision.py` - All random operations use seed `123`
- [x] `code/analysis/exploratory.py` - All random operations use seed `456`
- [x] No stochastic operations without pinned seeds detected

## Census Data Exception

Per Constitution Principle VII and FR-006, the core knot dataset is a census (complete enumeration of prime knots with crossing number ≤13). No random sampling is applied to the primary dataset itself. Random seeds are used only for:

1. Bootstrap resampling in regression validation
2. Precision estimation subsampling
3. Visualization example selection

## Related Documentation

- **T007**: Random seed pinning implementation in all code/ files
- **T058**: Seed verification report at `docs/reproducibility/seed_verification.md`
- **FR-007**: Reproducibility documentation requirements
- **Constitution Principle I**: Reproducibility through deterministic operations

## Update History

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-02 | 1.0 | Initial documentation per T050 |

## Verification Status

This document was generated as part of T050 implementation and verified against the following completed tasks:

- T007: Random seed pinning implementation ✓
- T032-T039: Regression analysis module (uses seed 42) ✓
- T022-T024: Precision and exploratory analysis (uses seeds 123, 456) ✓

## Notes

These seed values are documented for reproducibility purposes. Any changes to these values will be recorded in this document with appropriate version history updates. The seeds are intentionally chosen to be distinct across modules to allow independent verification of each stochastic operation's reproducibility.