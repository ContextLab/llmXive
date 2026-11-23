# User Story 1: Zero-Shot Adaptation to Unseen Damping

## Goal

Implement the full adaptive policy loop that detects friction via $k_{est}$ and
adjusts rewards, verifying >15% improvement over static baseline on novel
high-friction objects.

## Acceptance Criteria

- [ ] Virtual tactile estimator accurately estimates friction coefficient
- [ ] Adaptive reward scheduler adjusts weights based on $k_{est}$
- [ ] Novel object set includes high-friction variants
- [ ] Training loop integrates estimator and scheduler
- [ ] Evaluation compares adaptive vs static policies
- [ ] Statistical analysis confirms >15% improvement (p < 0.05)
- [ ] All tests pass (unit and integration)

## Implementation Details

### Estimator (FR-001)
- Formula: $k_{est} = \frac{\tau}{v}$ (torque/velocity ratio)
- Moving average filter (window=5)
- Epsilon clamping to prevent division by zero

### Scheduler (FR-002)
- If $k_{est} > 1.0$: increase $r_{detach}$ by ≥20%
- If $k_{est} < 0.2$: decrease $r_{contact}$ by ≤15%

### Object Generation (FR-003)
- Randomized articulated geometries
- Friction coefficients uniformly distributed across broad range

### Statistical Validation
- Paired t-test on success rates
- Effect size calculation for power analysis
- Sample size verification

## Test Cases

### Unit Tests
- `test_scheduler.py`: Verify weight scaling logic
- `test_estimator.py`: Verify division-by-zero protection and smoothing

### Integration Tests
- `test_pipeline.py`: Verify end-to-end success rate statistics

## Files

- `code/estimator.py`: VirtualTactileEstimator class
- `code/scheduler.py`: AdaptiveRewardScheduler class
- `code/generator.py`: NovelObjectSet generator
- `code/train.py`: Training loop integration
- `code/evaluate.py`: Policy comparison
- `code/aggregate.py`: Log aggregation
- `code/analysis.py`: Statistical analysis

## Dependencies

- T004: CPU-only PyBullet environment
- T005: VirtualTactileEstimator implementation
- T006: AdaptiveRewardScheduler implementation
- T007: NovelObjectSet generator

## Success Metrics

- **Primary**: >15% improvement in success rate for high-friction objects
- **Secondary**: p-value < 0.05 in paired t-test
- **Tertiary**: Statistical power ≥ 0.8
