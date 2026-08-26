# User Stories

## US1: Construct Discrete Privilege Illusion MDP Environment
**As a** researcher,
**I want** a synthetic MDP where the Teacher has a hidden privileged signal `H` and the Student only sees `O`,
**So that** I can study the impact of information asymmetry on policy learning.

**Acceptance Criteria**:
- Environment can be instantiated.
- Teacher observes `(O, H)`.
- Student observes only `O`.
- Optimal policy requires `H`.

## US2: Implement DOPD vs. Uniform Supervision Training Loops
**As a** researcher,
**I want** to compare DOPD and Uniform distillation on the MDP,
**So that** I can verify if dynamic weighting improves generalization when the Teacher's advantage is low.

**Acceptance Criteria**:
- Uniform training mimics Teacher actions.
- DOPD switches weighting based on advantage gap.
- Student shows higher entropy/self-correction in DOPD when Teacher advantage is low.

## US3: Execute Statistical Generalization Analysis
**As a** researcher,
**I want** to run a statistical comparison (Mann-Whitney U) of DOPD vs. Uniform generalization,
**So that** I can confirm if DOPD significantly outperforms Uniform supervision.

**Acceptance Criteria**:
- 50 independent seeds executed.
- P-value and effect size calculated.
- CV calculated for reproducibility.