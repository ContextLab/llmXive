# User Story 2: Virtual Tactile Stiffness Estimation

## Goal

Validate the $k_{est}$ estimator accuracy and stability under varying friction
and noise conditions.

## Acceptance Criteria

- [ ] Estimator maintains accuracy under noise injection
- [ ] Moving average filter provides stability
- [ ] Epsilon clamping prevents division by zero
- [ ] Linear correlation between $k_{est}$ and ground-truth friction
- [ ] Validation suite runs successfully
- [ ] All tests pass

## Implementation Details

### Estimator Features
- **Division-by-zero protection**: Epsilon clamping (FR-007)
- **Noise filtering**: Moving average (window=5)
- **Bounded range**: Clamping to valid friction coefficient range

### Stress Testing
- Noise injection at varying levels
- Stiction simulation
- Extreme friction conditions

### Validation
- Correlation analysis with ground-truth friction
- Stability variance calculation
- Real-time validation during episodes

## Test Cases

### Unit Tests
- `test_estimator.py`: Division-by-zero protection
- `test_estimator.py`: Moving average filter smoothing

### Integration Tests
- `test_estimator_clamping_integration.py`: FR-007 clamping logic

## Files

- `code/estimator.py`: VirtualTactileEstimator implementation
- `code/stress_test.py`: Noise injection tests
- `code/validation.py`: Estimator validation suite

## Dependencies

- T005: VirtualTactileEstimator implementation
- T017: FR-001 formula verification

## Success Metrics

- **Accuracy**: Correlation coefficient > 0.9 with ground-truth friction
- **Stability**: Variance under noise < 10% of signal
- **Robustness**: No crashes under extreme conditions
