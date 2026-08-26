# Project Specifications

## Functional Requirements
- **FR-001**: The Student's observation space must strictly exclude the privileged variable `H`.
- **FR-002**: DOPD must compute advantage gap and normalize it for dynamic weighting.
- **FR-005**: Statistical analysis must use Mann-Whitney U test.
- **FR-006**: Logging must capture training accuracy and convergence steps.
- **FR-007**: Evaluation seeds must be distinct from training seeds.
- **FR-008**: Grid dimension must ensure RAM usage < 7GB.

## Non-Functional Requirements
- **SC-003**: Report convergence steps.
- **SC-005**: Calculate Coefficient of Variation (CV) for reproducibility.
- **Performance**: 50 seeds must complete within the temporal constraint.

## Constraints
- Discrete state space only.
- No external API dependencies for data (use `gymnasium` or local generation).
- Python 3.9+.
