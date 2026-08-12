# Feature Specification: Self-improving LLM: recursive architecture refinement and re‑training

**Feature Branch**: `001-self-improving-llm-recursive-architectur`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "recursive architecture modification and re-training for LLM performance improvement"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1)

The researcher MUST be able to download a base model (GPT small), apply a single architectural modification proposed by the model (validated by an external oracle), re-train on a defined OpenWebText subset ([deferred] samples), and evaluate performance on GSM8K, ARC-Challenge, and BoolQ benchmarks. This establishes the fundamental pipeline before iterating.

**Why this priority**: Without a working single cycle, no recursive behavior can be studied. This is the minimum viable experiment that delivers the core research question answer for one iteration.

**Independent Test**: Can be fully tested by executing the pipeline once and verifying that performance metrics are recorded and compared against the pre-modification baseline.

**Acceptance Scenarios**:

1. **Given** a GPT-2 124M checkpoint is available on HuggingFace, **When** the pipeline downloads it, prompts the model to propose a modification (validated by FR-021), applies it, and re-trains for an epoch on a subset of [deferred] samples from OpenWebText, **Then** the modified model MUST be evaluated on GSMK (subset of samples), ARC-Challenge (subset of samples), and BoolQ (subset of samples) within 2 hours on a GitHub Actions free-tier runner (ubuntu-latest).
2. **Given** baseline metrics are recorded before modification, **When** the modified model completes training, **Then** the system MUST output accuracy for GSM8K, ARC-Challenge, and ECE for BoolQ with ≥3 decimal precision, derived from the specified sample sizes.
3. **Given** paired bootstrap statistical testing is configured, **When** baseline and post-modification metrics are available, **Then** the system MUST compute p-values for performance differences with significance threshold α = 0.05, bootstrapping over test set samples with a sufficient number of resamples.

---

### User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

The researcher MUST be able to iterate the refinement process three times (attempted cycles), recording performance after each cycle to identify whether gains persist, plateau, or degrade. This tests the core hypothesis about recursive improvement sustainability.

**Why this priority**: The research question specifically asks about persistence across cycles. Three cycles is the minimum to detect non-linear trajectories (improvement → plateau → degradation).

**Independent Test**: Can be fully tested by executing the pipeline for 3 consecutive cycles and verifying that performance metrics form a time-series with detectable trends.

**Acceptance Scenarios**:

1. **Given** cycle 1 completes successfully, **When** the pipeline proceeds to cycle 2, **Then** the system MUST apply a new architectural modification (distinct in type or magnitude from previous cycles, and proposed by the model based on its evaluation of cycle 1) while keeping total parameter count ≤30% above original GPT-2 baseline.
2. **Given** all three cycles complete, **When** performance metrics are aggregated, **Then** the system MUST output a performance trajectory table in JSON format at `results/trajectory.json` with cycle number, parameter count, GSM8K accuracy, ARC-Challenge accuracy, ECE, FLOPs, and training time.
3. **Given** performance trajectories are recorded, **When** analysis completes, **Then** the system MUST fit a linear regression model to the performance data and report the slope, intercept, R^2, and trend direction (improving/declining/flat).

---

### User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

The researcher MUST be able to compute cost-effectiveness metrics (performance per FLOP, performance per training hour) to determine whether recursive refinement is computationally viable compared to alternative improvement strategies.

**Why this priority**: Even if performance improves, the method is only valuable if it is compute-efficient. This analysis determines practical applicability.

**Independent Test**: Can be fully tested by computing trade-off ratios from recorded metrics and verifying that resource constraints are documented.

**Acceptance Scenarios**:

1. **Given** performance metrics and FLOPs are recorded for each cycle, **When** trade-off analysis executes, **Then** the system MUST compute performance-per-FLOP (accuracy / FLOPs) for GSM8K accuracy and ECE improvement.
2. **Given** training time is recorded for each cycle, **When** trade-off analysis executes, **Then** the system MUST compute performance-per-hour (accuracy / training_hours) for each benchmark.
3. **Given** the complete pipeline runs on a GitHub Actions free-tier runner, **When** job execution completes, **Then** total wall-clock time is measured (target ≤12 hours) and peak RAM usage is measured (target ≤7 GB) using system monitoring tools (psutil).

---

### Edge Cases

- What happens when the model's self-prompted suggestion proposes a modification that exceeds the parameter count constraint? The system MUST reject the modification (FR-003) and prompt the model again for an alternative within the constraint.
- How does the system handle training failure on a specific cycle? The system MUST retry up to 2 times with the same modification (FR-012); after 2 failed attempts, the cycle MUST be logged as failed, the cycle counter MUST increment, and the pipeline MUST proceed to the next cycle number with a new modification. A failed cycle counts as one of the three attempts (FR-007).
- What happens when paired bootstrap p-values are exactly 0.05? The system MUST treat p = 0.05 as non-significant (strictly p < 0.05 required for significance claim) (FR-006).
- How does the system handle dataset availability issues (e.g., HuggingFace API rate limits)? The system MUST implement exponential backoff with initial wait = 30 seconds, max retries = 5, and fail the job if all retries exhausted (FR-011).
- What happens when performance degradation occurs in cycle 2? The system MUST record the degradation cycle and terminate early if degradation ≥5% from baseline (Cycle 0) (FR-015).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a GPT checkpoint from HuggingFace and load it into a CPU-compatible PyTorch environment. The system MUST perform a 'Model Loader' step that explicitly sets device='cpu' and verifies the device is CPU (See US-1).
- **FR-002**: System MUST apply exactly one valid architectural modification (type and magnitude determined by the model's self-prompted suggestion, distinct in type or magnitude from all previous cycles) per cycle attempt. Distinctness is defined as 'Hamming distance ≥ 1 on the architecture config vector or >5% change in parameter count' (See US-2).
- **FR-003**: System MUST constrain total parameter count increase to ≤30% above original GPT-2 baseline across all cycles. This check MUST occur BEFORE applying the modification. System MUST reject if >30%. Justification: Common practice in parameter-efficient fine-tuning to avoid over-parameterization (See US-2).
- **FR-004**: System MUST re-train each modified model for exactly 1 epoch on OpenWebText subset ([deferred] samples) with AdamW optimizer, batch size 4, learning rate 5e-5. The system MUST perform a 'Training Configuration' step that validates these hyperparameters before training (See US-1).
- **FR-005**: System MUST evaluate each cycle on GSMK (subset of samples, metric: reasoning accuracy), ARC-Challenge (subset of representative samples, metric: reasoning accuracy), and BoolQ (subset of a representative sample, metric: calibration ECE). The system MUST perform an 'Evaluation Phase' that executes these benchmarks in the order: GSM8K, ARC-Challenge, BoolQ (See US-1).
- **FR-006**: System MUST perform paired bootstrap statistical comparison between successive cycles with significance threshold α = 0.05, using a sufficient number of resamples with replacement. The system MUST execute this test in a dedicated 'Statistical Analysis' step (See US-1).
- **FR-007**: System MUST repeat the modify-train-evaluate loop for exactly three attempted cycles. A 'failed cycle' (where training failed 2 times) counts as one of the three attempted cycles (See US-2).
- **FR-008**: System MUST record FLOPs and parameter count for each cycle to enable cost-effectiveness analysis. FLOPs MUST be calculated via torch.profiler (or equivalent) and recorded with appropriate numerical precision. (See US-3).
- **FR-009**: System MUST fit a linear regression model to performance trajectories and report the slope, intercept, R-squared, and trend direction (improving/declining/flat). If the linear fit fails (e.g., NaN slope), report 'N/A' for slope and 'inconclusive' for trend (See US-2).
- **FR-010**: System MUST compute performance-per-FLOP (accuracy / FLOPs) and performance-per-hour (accuracy / training_hours) metrics for each cycle. Units: accuracy per FLOP (1e-12), accuracy per hour (1/h) (See US-3).
- **FR-011**: System MUST implement exponential backoff for HuggingFace API calls with initial wait = 30 seconds and max retries = 5. The system MUST fail the job if all retries are exhausted (See US-1).
- **FR-012**: System MUST retry failed training runs up to 2 times; after 2 failed attempts, the system MUST log the failure, increment the cycle counter, and proceed to the next cycle number with a new modification. A failed cycle counts as one of the three attempted cycles (See US-2).
- **FR-015**: System MUST terminate early if performance degradation ≥5% from baseline (Cycle 0). The system MUST perform a 'Termination Check' step after each cycle evaluation to compare current performance against Cycle 0 baseline (See Edge Cases).
- **FR-019**: System MUST perform a 'Parameter Constraint Check' step before applying any modification to ensure the total parameter count does not exceed the [deferred] limit (See FR-003).
- **FR-020**: System MUST perform a 'Distinctness Validator' step to track previous modifications and ensure the new proposal is distinct (See FR-002).
- **FR-021**: System MUST perform an 'External Oracle Check' step to validate the model's proposed modification against a fixed, external heuristic (e.g., parameter efficiency) before application, breaking the circular validation loop (See US-2).

### Key Entities

- **ModelCheckpoint**: Represents a trained model instance with attributes: cycle_number, parameter_count, architecture_modification, training_time, flops
- **PerformanceMetric**: Represents evaluation results with attributes: cycle_number, benchmark_name (GSM8K/ARC-Challenge/BoolQ), accuracy_or_ECE, p_value_vs_predecessor
- **RefinementCycle**: Represents one iteration of the pipeline with attributes: cycle_number, pre_modification_params, post_modification_params, training_duration, evaluation_results, success_status

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reasoning accuracy improvement on GSM8K and ARC-Challenge is measured against the pre-modification baseline using paired bootstrap (p < 0.05) (See US-1)
- **SC-002**: Calibration error (ECE) on BoolQ is measured against the pre-modification baseline using paired bootstrap (p < 0.05) (See US-1)
- **SC-003**: Performance trajectory persistence is measured across 3 cycles by fitting a linear regression model and reporting the slope and trend direction (improving/declining/flat) (See US-2)
- **SC-004**: Cost-effectiveness is measured as performance-per-FLOP and performance-per-hour, compared across cycles to identify diminishing returns (See US-3)
- **SC-005**: Compute feasibility is measured by total wall-clock time (target ≤12 hours) and peak RAM usage (target ≤7 GB) on GitHub Actions free-tier runner, measured using system monitoring tools (psutil) (See US-3)

---

## Assumptions

- HuggingFace Datasets (OpenWebText subset, GSM8K, ARC-Challenge, BoolQ) will remain publicly accessible without authentication requirements during the execution window.
- PyTorch CPU backend with gradient checkpointing and batch size 4 will support GPT-2 124M model loading and training within the 7 GB RAM constraint (See FR-001, FR-004).
- The GitHub Actions free-tier runner will provide the specified multiple CPU cores, ~7 GB RAM, and Adequate disk space (See FR-001, FR-004).
- Paired bootstrap testing with a sufficient number of resamples will complete within the remaining time budget (See FR-006).
- The modification magnitude is determined by the model's self-prompted suggestion, validated by an external oracle (FR-021), not a fixed percentage or random integer.
- OpenWebText subset of [deferred] samples provides adequate training signal for detecting performance changes after 1 epoch of fine-tuning (See FR-004).
- The improvement criterion is fixed (performance on held-out OOD benchmarks) and NOT subject to modification during the 3-cycle experiment.
- Verification logic (evaluation on benchmarks) is logically separate from generative logic (model's self-prompted modification proposal) to prevent infinite regression (See FR-021).
- No CUDA, CUDA-accelerated operations, or 8-bit/4-bit quantization will be required or invoked.
- Constitution Principle V (Real-Call) is satisfied by performing statistical testing on real data loads (not mocked).
- Constitution Principle III (Data Hygiene) is satisfied by checksumming downloaded datasets and recording the hash in `data/`.
- Constitution Principle IV (Single Source of Truth) is satisfied by validating all data outputs against contracts in `contracts/`.
- The [deferred] parameter constraint is justified by common practice in parameter-efficient fine-tuning to avoid over-parameterization (See FR-003).
- The time target is a feasibility constraint.; the primary success criterion is the completion of the experiment (valid trajectory record), even if it exceeds 6 hours (See SC-005).
