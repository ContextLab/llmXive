# Feature Specification: Extending ZPPO with CAP

## User Stories

### US1: Static Baseline Simulation
As a researcher, I want to run the original ZPPO simulation with a static NCQ prompt so that I have a baseline convergence curve to compare against.

### US2: Confidence-Adaptive Pruning (CAP)
As a researcher, I want the system to dynamically prune negative candidates from the prompt based on the student's historical confidence (mean/variance) so that I can improve data efficiency by focusing on "fluctuating" candidates.

### US3: Comparative Statistical Analysis
As a researcher, I want to compare the AUCC and final accuracy of the Static vs. CAP runs using paired t-tests so that I can statistically validate the improvement.

## Functional Requirements
- **FR-001**: Synthetic rollout logs must simulate learning dynamics (expert gap, prompt length).
- **FR-002**: Static NCQ generator must include all known failure modes.
- **FR-003**: CAP classifier must exclude 'consistently rejected' (<0.1) and 'consistently accepted' (>0.9) candidates.
- **FR-004**: Dynamic NCQ generator must filter candidates based on CAP output.
- **FR-005**: Statistical analysis must calculate paired t-test and effect size.
- **FR-006**: Catastrophic forgetting check must compare held-out test accuracy.
- **FR-007**: Fallback to full candidate set if pruning results in an empty prompt.
- **FR-008**: Gaussian noise (σ=0.05) must be injected into confidence scores at every step.

## Non-Functional Requirements
- **NFR-001**: All data loaders must use real sources (MMLU) or fail loudly.
- **NFR-002**: Reproducibility via deterministic seed management.
- **NFR-003**: Performance: Simulation must complete within 6 hours on CPU.
