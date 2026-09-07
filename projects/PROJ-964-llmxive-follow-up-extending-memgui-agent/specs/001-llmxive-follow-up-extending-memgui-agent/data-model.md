# Data Model: llmXive follow-up: extending "MemGUI-Agent"

## Entity Definitions

### 1. SyntheticTrajectory
A sequence of mobile GUI states and actions spanning 50–100 steps.
*   **ID**: `str` (UUID)
*   **Steps**: `List[Step]`
*   **DependencyLinks**: `List[DependencyLink]` (Annotated ground truth)
*   **Source**: `str` (e.g., "Proc-Gen-001")
*   **PlausibilityScore**: `float` (0.0–1.0, from coherence validator)

### 2. Step
A single interaction in the trajectory.
*   **Index**: `int` (0 to N-1)
*   **State**: `str` (Text description of GUI state, e.g., "Settings > WiFi")
*   **Action**: `str` (Ground truth action, e.g., "Tap 'Connect'")
*   **Output**: `str` (Agent's predicted action)
*   **Success**: `bool` (1 if Agent Output == Action, else 0)
*   **Latency**: `float` (seconds)
*   **MemoryFootprint**: `float` (MB)
*   **Condition**: `str` (e.g., "baseline", "recall", "noise", "shuffled")

### 3. DependencyLink
An annotation indicating a critical information dependency.
*   **SourceStepIndex**: `int` (The step where info was introduced)
*   **TargetStepIndex**: `int` (The step where info is needed)
*   **InfoSnippet**: `str` (The text content that must be retained)
*   **Distance**: `int` (Target - Source)

### 4. MemoryFlash
A retrieved snippet injected into the prompt.
*   **RetrievedSnippet**: `str`
*   **SourceIndex**: `int`
*   **SimilarityScore**: `float`
*   **InjectionStep**: `int`

### 5. ExecutionLog
Aggregated results for a trajectory (per condition).
*   **TrajectoryID**: `str`
*   **Condition**: `str` (e.g., "baseline", "recall")
*   **SuccessRate**: `float` (0.0–1.0)
*   **LatencyAvg**: `float`
*   **MemoryPeak**: `float`
*   **StepCount**: `int`

## Data Flow

1.  **Generation**: `synthetic_benchmark.py` reads state templates -> Chains them -> Annotates `DependencyLinks` -> Outputs `synthetic_benchmark.jsonl`.
2.  **Validation**: `coherence_validator.py` scores chains -> Discards low-plausibility ones.
3.  **Baseline Run**: `base_conact.py` loads `synthetic_benchmark.jsonl` -> Executes agent -> Logs `ExecutionLog` (Condition="baseline") to `logs/baseline/`.
4.  **Recall Run**: `recall_agent.py` loads `synthetic_benchmark.jsonl` -> Builds Index -> Executes agent with injection -> Logs `ExecutionLog` (Condition="recall") to `logs/recall/`.
5.  **Control Runs**: `recall_agent.py` runs with noise/shuffled history -> Logs `ExecutionLog` (Condition="noise"/"shuffled").
6.  **Analysis**: `stats.py` reads all logs -> Performs Mixed-Effects Logistic Regression (GLMM) -> Outputs `results/stats_summary.json`.


## Statistical Model Specification (GLMM)

*   **Formula**: `Success ~ Condition + (1 | TrajectoryID) + (1 | StepIndex)`
*   **Link Function**: Logit
*   **Distribution**: Binomial
*   **Fixed Effect**: `Condition` (Baseline vs. Recall vs. Noise vs. Shuffled)
*   **Random Effects**: `TrajectoryID` (accounts for trajectory-level variance), `StepIndex` (accounts for temporal decay).
*   **Primary Metric**: Odds Ratio of `Condition_recall` vs `Condition_baseline`.