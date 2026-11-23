# API Reference

## Environment
- `code/env/privilege_mdp.py`
 - `PrivilegeMDP`: The core MDP environment.
 - `reset(seed)`: Resets environment, returns observation `O`.
 - `step(action)`: Returns `(next_obs, reward, terminated, truncated, info)`.
 - `get_full_state()`: Returns `(O, H)` for Teacher.

## Agents
- `code/agents/teacher.py`
 - `TeacherOracle`: Optimal policy agent.
- `code/agents/student.py`
 - `TabularQStudent`: Q-learning agent with epsilon-greedy exploration.
- `code/agents/baseline_estimator.py`
 - `BaselineEstimator`: Estimates `V(s)` for a random policy.

## Training
- `code/training/uniform_distillation.py`
 - `UniformDistillationTrainer`: Standard distillation.
- `code/training/dopd_distillation.py`
 - `DOPDTrainer`: Dynamic On-Policy Distillation.

## Analysis
- `code/analysis/generalization_test.py`
 - `evaluate_agent_in_masked_mode`: Evaluates agent without privileged info.
 - `calculate_performance_drop`: Computes metric.
- `code/analysis/stats.py`
 - `run_mann_whitney_test`: Statistical comparison.

## Utilities
- `code/utils/seeding.py`: Deterministic seeding utilities.
- `code/utils/logging.py`: Structured logging for training metrics.
