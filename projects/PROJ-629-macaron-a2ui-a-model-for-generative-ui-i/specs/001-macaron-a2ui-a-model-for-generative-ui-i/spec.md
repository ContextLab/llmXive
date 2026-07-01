# Feature Specification: Macaron-A2UI Reproduction & Validation

**Feature Branch**: `001-macaron-a2ui-reproduction`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Macaron-A2UI: A Model for Generative UI in Personal Agents"

## User Scenarios & Testing

### User Story 1 - Automated Execution of Evaluation Pipeline (Priority: P1)

As a researcher, I need to execute the vendored `Macaron-A2UI-Bench` evaluation script on a CPU-only CI runner so that I can verify the codebase runs end-to-end and produces the primary evaluation artifacts without requiring GPU hardware.

**Why this priority**: This is the foundational step. If the code cannot execute on the available free-tier infrastructure (Multiple CPU, 7GB RAM), the project cannot proceed to validation or reproduction of results. It addresses the core constraint of the project environment.

**Independent Test**: The CI job completes successfully (exit code 0), and the output directory contains the generated evaluation JSON report and any intermediate log files, regardless of whether the numerical scores match the paper.

**Acceptance Scenarios**:
1. **Given** the `Macaron-A2UI-Bench` submodule is checked out, **When** the `evaluate_api_model.py` script is invoked with the default CPU-compatible configuration, **Then** the script terminates within 6 hours and writes a valid JSON report to `results/evaluation_report.json`.
2. **Given** the environment lacks a CUDA device, **When** the script attempts to load the model or run inference, **Then** the system defaults to CPU execution (e.g., `device="cpu"`) and does not crash with a CUDA-related error.

---

### User Story 2 - Artifact Generation and Visualization (Priority: P2)

As a reviewer, I need the evaluation run to generate the specific visual comparison artifacts (PNG images) and renderable data files so that I can visually inspect the generated UI states and confirm the "Generative UI" aspect of the model is functioning.

**Why this priority**: The paper's core claim is about generating *UI*, not just text. Without visual artifacts, the reproduction is incomplete. This validates the specific domain capability (UI generation) distinct from general NLP.

**Independent Test**: The run produces a set of PNG images in the `render/public/showcase/` directory corresponding to the evaluated tasks, and the `render/` directory can be served to display these comparisons.

**Acceptance Scenarios**:
1. **Given** the evaluation script completes, **When** the `render_check.py` or equivalent visualization script is run, **Then** at least 10 distinct PNG comparison images are generated in `render/public/showcase/qwen-235b-rl/images/compare/` matching the task IDs in the input data.
2. **Given** the generated data JSON files, **When** the `render/index.html` is opened in a browser (or headless browser), **Then** the UI components are rendered correctly without broken image links or missing DOM elements.

---

### User Story 3 - Quantitative Score Validation (Priority: P3)

As a stakeholder, I need the evaluation pipeline to calculate and report the "Overall" score and sub-metrics (e.g., consistency, execution rate) so that I can compare the reproduced results against the paper's claimed score on A2UI-Bench.

**Why this priority**: This provides the final verification of the paper's quantitative claims. While P1 and P2 ensure the system works, P3 ensures it works *as claimed*. This is the final validation step.

**Independent Test**: The evaluation report contains a numeric "Overall" score and the script outputs a summary table comparing the reproduced score to the paper's reported baseline.

**Acceptance Scenarios**:
1. **Given** the evaluation report is generated, **When** the `evaluate_api_model.py` summary is printed, **Then** it displays a numeric score for "Overall" accuracy and lists sub-scores for each dataset (annomi, esconv, multiwoz, sgd).
2. **Given** the paper claims a score of 75.6, **When** the reproduced score is calculated, **Then** the system logs the difference (delta) between the reproduced score and the paper's claim, flagging if the delta exceeds a pre-defined significance margin (for debugging purposes).

---

### Edge Cases

- **Memory Overflow**: What happens if the model context or batch size exceeds the GB RAM limit on the free-tier runner? (Handled by enforcing batch size = 1 or sub-sampling in `Assumptions`).
- **Missing Dependencies**: How does the system handle missing Python packages in the vendored `vendor/` directory? (Handled by a strict `pip install -r requirements.txt` step in the run-book).
- **Timeout**: If the evaluation of a single task exceeds minutes, does the job fail or skip? (Handled by a hard timeout for the total job).

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `evaluate_api_model.py` script using CPU-only inference without requiring CUDA or GPU acceleration (See US-1).
- **FR-002**: System MUST generate at least 10 valid PNG comparison images representing the generated UI states for the evaluated tasks (See US-2).
- **FR-003**: System MUST produce a structured JSON evaluation report containing the "Overall" score and per-dataset sub-scores (See US-3).
- **FR-004**: System MUST handle the `annomi`, `esconv`, `multiwoz`, and `sgd` datasets from the `data/eval_300` directory without crashing due to missing files (See US-1).
- **FR-005**: System MUST complete the full evaluation pipeline within a maximum runtime of several hours on a 2-core CPU environment (See US-1).

### Key Entities

- **Evaluation Report**: A JSON artifact containing metrics (Overall, Consistency, Execution Rate) and task-level results.
- **UI Artifact**: A PNG image file visualizing the generated UI component compared to the ground truth.
- **Task Instance**: A single dialogue instance from the A2UI-Bench datasets (e.g., `annomi_tasks.json`) used as input for generation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The reproducibility success rate is measured against the binary outcome of the CI job (Pass/Fail), where "Pass" requires exit code 0 and artifact generation (See FR-001, FR-002).
- **SC-002**: The visual artifact completeness is measured against the count of expected task instances in `data/eval_300/manifest.json`, requiring ≥ 10 successful image generations (See FR-002).
- **SC-003**: The quantitative score deviation is measured against the paper's reported "Overall" score of 75.6, with a target delta ≤ 5.0 points for a successful validation (See FR-003).
- **SC-004**: The resource feasibility is measured against the free-tier runner constraints (Limited CPU resources, 7GB RAM, 6h limit), requiring zero OOM or timeout errors (See FR-001, FR-005).
- **SC-005**: The dataset coverage is measured against the four source datasets (annomi, esconv, multiwoz, sgd), requiring successful processing of ≥ 1 instance from each (See FR-004).

## Assumptions

- The vendored `Macaron-A2UI-Bench` repository contains all necessary dependencies and can be installed via standard `pip` commands without manual intervention.
- The model weights required for inference are either included in the submodule or can be downloaded via a public Hugging Face link without authentication; if weights are missing, the spec assumes a smaller, CPU-tractable model (e.g., a Large-scale parameter model

The research question, the method, and the references remain as stated in the original planning document. with -bit quantization *if* the library supports CPU-only bitsandbytes fallback, otherwise a standard Large-scale FP16 model

The research question investigates the scalability of large-scale language models, the method involves comparative analysis of architectural efficiency, and the references include the foundational work on scaling laws (Kaplan et al., 2020).) will be substituted to ensure the run completes within the 6-hour limit.
- The `render/` directory contains a pre-built `index.html` that does not require a build step (e.g., no `npm run build`) to display artifacts, or the build step is included in the execution script.
- The evaluation script `evaluate_api_model.py` can be configured to use a smaller batch size (e.g., `batch_size=1`) to fit within the 7GB RAM limit, even if this increases runtime.
- The paper's claim of "75.6 overall" refers to a specific metric defined in the paper's appendix or `evaluate_api_model.py` logic, which will be identified during the initial code inspection.
