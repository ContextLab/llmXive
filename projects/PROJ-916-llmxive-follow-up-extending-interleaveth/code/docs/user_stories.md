# User Stories

## US1: Construct Text-Based Scene Simulator

**Goal**: Implement a deterministic text-based simulator that converts image prompts into structured JSON scene descriptions with controllable "Noisy Mode" to simulate the grounding gap.

**Acceptance Criteria**:
- Simulator invoked with prompt string and mode flag ("Perfect" or "Noisy")
- Returns valid JSON within 500ms
- Contains keys: `objects`, `relationships`, `attributes`
- No external image generation API calls

**Tasks**:
- T012: Implement `src/simulator/parser.py`
- T013: Implement `src/simulator/noise_injector.py`
- T014: Implement `src/simulator/simulator.py`
- T015: Implement `src/benchmarks/loader.py`
- T016a/T016b: Implement `src/stats/simulator_metrics.py`
- T017: Implement `src/simulator/validator.py`
- T018a/T018b: Implement `src/stats/generator_metrics.py` and deterministic seeding

## US2: Execute CPU-Tractable Agentic Loop

**Goal**: Execute the full agentic pipeline using a lightweight LLM on CPU.

**Acceptance Criteria**:
- Processes benchmark samples from WISE/RISE
- Completes planning-generating-critic loop
- Outputs JSON log of reasoning scores (F1-score)
- Runtime ≤ 6 hours, RAM ≤ 7GB

**Tasks**:
- T022: Implement `src/agents/critic.py` and interfaces
- T023: Implement `src/agents/planner.py`
- T024: Implement `src/agents/generator.py`
- T025: Implement `src/pipeline/orchestrator.py`
- T026: Implement memory management
- T027: Implement `src/metrics/reasoning_score.py`
- T028: Add logging for `TrajectoryLog`
- T029: Implement "warm-up" logic
- T030: Implement "timeout" mechanism

## US3: Perform Statistical Comparison and Ablation

**Goal**: Perform statistical analysis and ablation study to quantify the value of structural decomposition.

**Acceptance Criteria**:
- Outputs report with p-values and effect sizes
- Compares "Full Loop" vs. "No-Critic" performance
- Handles missing pre-computed image-based results gracefully

**Tasks**:
- T031: Implement paired t-tests and Wilcoxon tests
- T032: Calculate effect sizes (Cohen's d)
- T033: Implement "No-Critic" baseline run
- T034: Generate statistical significance report
- T036: Calculate statistical power
