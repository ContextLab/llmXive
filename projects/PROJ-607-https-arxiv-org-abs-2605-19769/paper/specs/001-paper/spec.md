# Feature Specification: Verifiable Software Worlds: A Reproduction and Qualitative Validation of OpenComputer

**Feature Branch**: `607-reproduce-opencomputer`
**Created**: 2026-07-01
**Status**: Draft
**Input**: User description: "Synthesize the research-stage reproduction of OpenComputer into a formal paper specification, focusing on the qualitative validation of verifier alignment against human adjudication in a constrained CI environment."

## User Scenarios & Testing

### User Story 1 - Reproduce the Pipeline Viability (Priority: P1)

**Describe this user journey**: A peer reviewer or follow-up researcher executes the provided "Smoke Test" script to verify that the OpenComputer environment provisioning, task execution, and verification loops function correctly on a standard CPU-only CI runner, establishing the baseline viability of the reproduction.

**Why this priority**: This is the "smoke test" required to confirm the vendored code is not broken by the submodule integration. If the basic execution loop fails, no further validation of the paper's claims is possible. It establishes the foundational reproducibility of the system.

**Independent Test**: Run the provided smoke loop script (`run_smoke_test.sh`) against a single, simple task (`audacity_export_wav_440`) within a Docker container. Success is defined by the script exiting with code 0 and generating a valid `smoke_report.json` artifact with a status of "success" or "partial_success".

**Acceptance Scenarios**:
1. **Given** the Docker daemon is running and the `external/OpenComputer` submodule is cloned, **When** the user executes the smoke test wrapper, **Then** the system provisions a container, runs the task, and outputs a `smoke_report.json` confirming the pipeline is operational.
2. **Given** the Docker daemon is running but the required base image is missing, **When** the user runs the smoke test, **Then** the system attempts to build the image via `build_image.sh` and proceeds to execution, or fails explicitly with a "build_failed" status and detailed error log.

---

### User Story 2 - Validate Verifier Alignment via Blinded Inspection (Priority: P2)

**Describe this user journey**: A researcher executes a small batch of tasks (N=5) and compares the OpenComputer verifier's pass/fail judgment against a "blinded, independent human adjudication" of the generated artifacts to confirm the verifier's fidelity, acknowledging the qualitative nature of the study.

**Why this priority**: The core claim of the paper is that OpenComputer's verifiers align better with human adjudication than LLM-as-judge. Validating this alignment on a sample set is the primary scientific contribution. The study explicitly pivots from statistical margins to a qualitative narrative due to sample size constraints (N=5), ensuring scientific integrity.

**Independent Test**: Run 5 distinct tasks. Manually inspect the generated artifacts (e.g., the exported audio file or modified document) and compare the result against the verifier's JSON output. The test passes if the verifier correctly identifies the success/failure state as confirmed by manual inspection, documented in `blinded_ground_truth.json`.

**Acceptance Scenarios**:
1. **Given** a set of 5 tasks with known ground-truth outcomes, **When** the `run_batch_eval.sh` script executes these tasks, **Then** the `verification_report.json` contains a qualitative `alignment_observation` narrative that accurately reflects the matches and mismatches between the verifier and the manual ground truth.
2. **Given** a task that fails mid-execution, **When** the system runs the verification step, **Then** the verifier correctly flags the task as "failed" and records the specific state mismatch (e.g., "file_not_found") in the `failure_reason` field, which is then cross-referenced with the manual inspection notes.

---

### User Story 3 - Generate Reproduction Report with Limitations (Priority: P3)

**Describe this user journey**: The system aggregates the results from the smoke tests and validation runs to generate a final `reproduction_report.md` that explicitly states whether the paper's claims regarding "desktop applications" and "finalized tasks" are reproducible within the constraints of the free-tier CI environment, including a dedicated "Limitations" section.

**Why this priority**: This synthesizes the technical execution into the final deliverable required for the project to reach `research_complete`. It answers the "So what?" question for the reproduction effort and ensures transparency regarding the N=5 sample size and CPU-only constraints.

**Independent Test**: Execute the `generate_report.py` script which reads the JSON artifacts from US-01 and US-02. The test passes if the generated markdown file contains a "Conclusion" section that explicitly references the success rate, compares it to the paper's abstract claims, and includes a "Limitations" section detailing the N=5 constraint and the qualitative methodology.

**Acceptance Scenarios**:
1. **Given** successful JSON artifacts from US-01 and US-02, **When** the report generation script runs, **Then** the output `reproduction_report.md` contains a table summarizing the `tasks_attempted`, `tasks_passed`, and a qualitative `alignment_observation`, explicitly stating "Claims Partially Reproduced" based on the data.
2. **Given** a runtime error occurs during the batch execution (e.g., container timeout), **When** the report generation script runs, **Then** the report includes a "Limitations" section detailing the specific error and the number of tasks skipped, rather than failing to generate the file.

### Edge Cases

- **Given** the Docker backend runs out of disk space (limit ~14 GB) during image build, **When** the provisioning step occurs, **Then** the system fails gracefully with a "disk_quota_exceeded" error and does not attempt to run the task.
- **Given** an agent (e.g., `gemini_agent`) requires an API key that is not provided in the environment, **When** the agent initialization occurs, **Then** the system skips that agent and logs a "missing_credentials" warning rather than crashing the entire pipeline.
- **Given** a task requires a specific GUI application (e.g., GIMP) that is not installed in the Docker base image, **When** the task runner attempts to launch the app, **Then** the verifier records a "dependency_missing" failure and the task is marked as "skipped" in the report.
- **Given** the manual inspection reveals a discrepancy between the verifier and the artifact, **When** the report is generated, **Then** the `alignment_observation` narrative explicitly describes the nature of the discrepancy (e.g., "Verifier passed, but file format was incorrect") rather than aggregating it into a misleading metric.

## Required Sections

The paper must contain the following sections to satisfy the Tasker and Reader requirements:

1. **Abstract**: Summarize the reproduction effort, the pivot to qualitative validation, and the primary findings regarding verifier alignment.
2. **Introduction**: Contextualize OpenComputer, state the hypothesis (verifier alignment), and define the scope constraints (N=5, CPU-only).
3. **Methods**: Detail the "Blinding Protocol," the Docker environment setup, the specific tasks selected (from `data/`), and the scripts used (`run_smoke_test.sh`, `run_batch_eval.sh`).
4. **Results**: Present the `smoke_report.json` status, the `verification_report.json` data, and the qualitative `alignment_observation` narrative. Include the `blinded_ground_truth.json` summary.
5. **Discussion**: Interpret the alignment results, discuss the "Engine vs. Agent" distinction (ordering precision), and analyze the limitations of the N=5 sample size.
6. **References**: Cite the original OpenComputer paper and any relevant tools used.
7. **Appendix**: Include the exact command lines used for reproduction and the schema definitions for the JSON artifacts.

## Required Figures

The following figures must be generated from the existing data artifacts to support the narrative:

1. **Figure 1: Pipeline Architecture Diagram**: A schematic showing the flow from Task Definition → Docker Provisioning → Agent Execution → Verifier Judgment → Blinded Manual Inspection. (Source: `data-model.md` and `plan.md` technical context).
2. **Figure 2: Verifier vs. Manual Adjudication Matrix**: A visual representation (table or heatmap) of the 5 tasks showing the Verifier Verdict vs. the Manual Ground Truth, highlighting matches and mismatches. (Source: `data/verification_results.csv` and `data/blinded_ground_truth.json`).
3. **Figure 3: Execution Timeline & Error Log**: A timeline showing the duration of the smoke test and batch execution, highlighting any "skipped" or "failed" states due to resource constraints. (Source: `logs/smoke.log` and `verification_report.json`).

## Required Claims

The paper will make the following inferential claims, which will be verified by the Reference-Validator against the research artifacts:

1. **Claim 1**: The OpenComputer pipeline is reproducible on a standard CPU-only CI runner with a free-tier disk quota (≤14 GB). [UNRESOLVED-CLAIM: c_748ef54c — status=not_enough_info]
 * *Verification Target*: Success of `run_smoke_test.sh` and `smoke_report.json` status.
2. **Claim 2**: The `hardcode` verifiers demonstrate high alignment with human adjudication on a sample set of 5 tasks, despite the inability to calculate a statistical margin of error.
 * *Verification Target*: The qualitative `alignment_observation` in `verification_report.json` and the `blinded_ground_truth.json` data.
3. **Claim 3**: The system acts as a precise "engine" for executing task definitions, with failures primarily attributed to agent "origination" (deviation) or environmental dependencies rather than system instability.
 * *Verification Target*: The "Engine vs. Agent" section in `reproduction_report.md` and the analysis of `step_execution_count` vs `total_steps` from T035.
4. **Claim 4**: The "10% margin of error" requirement in the original specification is scientifically invalid for N=5, and a qualitative narrative is the appropriate methodological alternative.
 * *Verification Target*: The "Limitations" section in `reproduction_report.md` and the explicit logic in `compare_verdicts.py` (T026b).

## Edge Cases (Paper Specific)

- **Ambiguous Artifacts**: If a generated artifact (e.g., a resized image) is visually ambiguous regarding success/failure, the "Blinding Protocol" must document the specific criteria used by the human adjudicator to make a binary decision.
- **Repeated Content**: If the `reproduction_report.md` generation logic detects that the `alignment_observation` narrative is identical to the raw log output, the proofreader must flag this for expansion into a true qualitative analysis.
- **Missing Dependencies**: If a task in the sample set fails due to a missing GUI dependency (e.g., GIMP), the paper must explicitly distinguish this "environmental failure" from an "agent failure" in the Results section.

## Requirements

### Functional Requirements

- **FR-001**: The paper MUST include a "Methods" section that explicitly details the "Blinding Protocol" used to anonymize artifacts for manual inspection, ensuring independence from the verifier's logic.
- **FR-002**: The paper MUST present the results of the smoke test and the N=5 batch execution, including the `smoke_report.json` and `verification_report.json` summaries.
- **FR-003**: The paper MUST replace any statistical claims (e.g., "10% margin") with a qualitative narrative `alignment_observation` that describes the specific matches and mismatches between the verifier and human adjudication.
- **FR-004**: The paper MUST include a "Limitations" section that explicitly states the constraints of the study (N=5 sample size, CPU-only environment, free-tier CI disk quota) and explains why these prevent broader statistical generalization.
- **FR-005**: The paper MUST address the "Engine vs. Agent" distinction by analyzing the agent's adherence to the task definition sequence (ordering precision) rather than just the final outcome.
- **FR-006**: The paper MUST reference the specific data artifacts (`blinded_ground_truth.json`, `verification_results.csv`) as the source of truth for the validation results.

### Success Criteria

- **SC-001**: The `reproduction_report.md` is generated and contains a "Conclusion" section that explicitly states "Claims Partially Reproduced" or "Claims Reproduced" based on the qualitative data.
- **SC-002**: The `alignment_observation` narrative accurately reflects the data in `blinded_ground_truth.json` without attempting to calculate a statistical rate.
- **SC-003**: The "Engine vs. Agent" analysis section is present and discusses the agent's step adherence based on the logs generated in T035.
- **SC-004**: The paper explicitly acknowledges the impossibility of the original "10% margin" requirement and justifies the qualitative approach.
- **SC-005**: All figures (Architecture, Matrix, Timeline) are generated from the actual data files in `data/` and `results/`.

## Assumptions

- The local Docker daemon is available and functional on the CI runner, allowing for the build and execution of the OpenComputer environment images.
- The `external/OpenComputer` submodule is correctly cloned and contains all necessary dependencies as listed in `requirements.txt` without modification.
- The free-tier CI runner (multiple CPU cores, adequate RAM) is sufficient to run the Docker containers for the selected sample tasks, assuming no heavy GPU-accelerated models are invoked.
- The `hardcode` verifiers provided in the `evaluation/apps/specs/` directory are sufficient to validate the tasks in the sample set without requiring additional configuration.
- Network access is available to pull base Docker images if they are not locally cached.
- The paper's claim of a "large corpus of finalized tasks" refers to the total corpus, but the reproduction scope is limited to a representative sample (N=5) due to compute constraints.
- The human adjudicator (simulated or real) follows the "Blinding Protocol" strictly to avoid confirmation bias.

## Notes for Paper-Clarifier

- **NEEDS CLARIFICATION**: The specific "ordering metric" to be used for the "Engine vs. Agent" analysis (T035a) needs final definition in the Methods section (e.g., exact step sequence vs. total steps).
- **NEEDS CLARIFICATION**: The exact visual style for Figure 2 (Matrix) needs to be confirmed (e.g., heatmap vs. simple table) to ensure clarity for the reader.
- **NEEDS CLARIFICATION**: Whether the "Limitations" section should include a specific recommendation for future work (e.g., "A larger sample size is required for statistical significance") or simply state the constraint.
