# Design Document: Discrete Privilege Illusion MDP

## 1. System Architecture
The system consists of three main components:
1. **Environment (`PrivilegeMDP`)**: A grid-world MDP with a hidden state `H` (privileged)
 and an observable state `O`. The Teacher sees `(O, H)`, while the Student sees only `O`.
2. **Agents**:
 - `TeacherOracle`: Optimal policy using full state `(O, H)`.
 - `TabularQStudent`: Q-learning agent using partial state `O`.
3. **Training Regimes**:
 - `UniformDistillation`: Fixed-weight imitation of Teacher actions.
 - `DOPD`: Dynamic weighting based on the advantage gap between Teacher and a baseline.

## 2. State Space Definition
- **Grid Size**: `N x M` (configurable, constrained by RAM).
- **Hidden State `H`**: Binary signal (0 or 1) indicating the "correct" direction or goal.
- **Observable State `O`**: Current grid coordinates `(x, y)`.
- **Full State**: `(x, y, H)`.
- **Observation (Student)**: `(x, y)`.

## 3. Transition Dynamics
- The agent moves in the grid.
- Reward is given upon reaching a goal state, which depends on `H`.
- If `H` is masked, the Student cannot determine the optimal goal without exploration or teacher guidance.

## 4. Privilege Mechanism
- The `PrivilegeMDP` enforces that `H` is strictly excluded from the Student's observation space.
- The Teacher's observation space includes `H`.
- This creates an information asymmetry necessary for the distillation study.

## 5. Training Logic
- **Uniform**: Student minimizes cross-entropy with Teacher's action distribution.
- **DOPD**:
 1. Compute Advantage: `A(s, a) = Q_Teacher(s, a) - V_Baseline(s)`.
 2. Normalize Advantage.
 3. Weight distillation loss: `L = w * CE(Teacher) + (1-w) * SelfSup`.
 4. `w` is high when Advantage is high (Teacher is confident/better), low otherwise.

## 6. Evaluation
- **Masked Evaluation**: Evaluate Student with `H` masked (standard mode).
- **Performance Drop**: `(Acc_Unmasked - Acc_Masked) / Max_Reward`.
- **Statistical Test**: Mann-Whitney U test to compare DOPD vs. Uniform generalization.
