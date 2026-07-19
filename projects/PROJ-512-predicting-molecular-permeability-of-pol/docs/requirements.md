# Requirements Specification Summary

## Functional Requirements (FR)
- **FR-001**: Use ONLY 2D graph features (atom type, hybridization, bond type).
- **FR-002**: Support NIST data fetch with simulation fallback.
- **FR-003**: Implement Murcko scaffold splitting.
- **FR-004**: CPU-only execution.
- **FR-005**: Reproducible random seeds.

## Non-Functional Requirements
- **Performance**: Training must complete within time limits on CPU.
- **Memory**: Peak RSS must be optimized (target < 10% reduction via optimization).
- **Reliability**: Fail loudly on data fetch errors; no silent synthetic fallbacks without logging.

## Constraints
- No 3D features.
- No GPU usage.
- Strict scaffold split (no scaffold overlap between train/test).
