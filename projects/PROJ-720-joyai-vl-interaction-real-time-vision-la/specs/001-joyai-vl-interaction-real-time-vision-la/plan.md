# Implementation Plan: JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence Reproduction

**Branch**: `720-joyai-vl-interaction-reproduction` | **Date**: 2024-05-22 | **Spec**: `specs/720-joyai-vl-interaction-reproduction/spec.md`
**Input**: Feature specification from `/specs/720-joyai-vl-interaction-reproduction/spec.md`

## Summary

This project reproduces and validates the "JoyAI-VL-Interaction" system, focusing on real-time decision-making (respond, stay silent, delegate) based on video input. The primary constraint is execution on a CPU-only GitHub Actions runner with a limited number of cores and constrained RAM without GPU acceleration.

**Critical Scope Reframe**: The original spec claims "human preference over existing assistants" (SC-007). This claim **cannot** be validated in a CI environment without human raters. Therefore, this plan explicitly reframes SC-007 to measure **"Logic Fidelity"** (does the system correctly implement the decision logic?) and **"Artifact Completeness"** (does it produce all required outputs?). The "human preference" claim is explicitly marked as **Unvalidated in CI** and requires an external human study. The plan does NOT claim to validate superiority; it validates that the system logic matches the paper's described behavior.

The technical approach involves adapting a vision-language model (VLM) for CPU inference (using quantization or a smaller distilled variant if the 8B model is infeasible), simulating the video stream with sampled frames, and integrating mock or lightweight versions of ASR, TTS, Memory Summarizer, Background Agent, and Visualization services to validate the pipeline logic and decision artifacts without external dependencies.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `accelerate`, `pillow`, `opencv-python-headless`, `pytest`, `pyyaml`, `fastapi` (for lightweight service simulation if needed), `pydantic`.  
**Storage**: Local file system (for artifacts/logs), `memory` (in-memory data structures for session state).  
**Testing**: `pytest` with `unittest.mock` for component isolation.  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Reproduction/Research Pipeline.  
**Performance Goals**: Inference latency < 10 mins per sample sequence; Total pipeline < 2 hours; Memory footprint < 6 GB.  
**Constraints**: No GPU/CUDA; No external API calls for core logic (mocked); -hour CI limit.  
**Scale/Scope**: Single feature reproduction; Sample dataset (a small number of video clips); decision types validated.

> **Dataset Variable Fit Note**: The spec assumes the existence of a "sample video stream" and "recorded real-world scenario". Since no external dataset URL is provided in the verified block, the implementation will use a synthetic or minimal local sample set (e.g., public domain video clips or generated frames) to validate the *logic* of the decision engine, acknowledging that full human preference validation (SC-007) is qualitative and limited by the sample size.

## Constitution Check

**Note**: No `constitution.md` file was supplied for this project. In the absence of a project-specific constitution, this plan adheres to the following fallback principles (FR-030) and explicitly maps to them:

1.  **Principle I (SSoT)**: Adhered to by designating `spec.md` as the Single Source of Truth for all reproduction logic. All deviations (e.g., model size) are documented against the spec. This plan explicitly confirms that `spec.md` is the SSoT.
2.  **Principle V (Real-Call Testing)**: Adhered to by performing real model inference (CPU-optimized) and mocking only external/heavy dependencies (ASR, TTS, Agent) that would violate CI constraints. This plan explicitly confirms that core logic is tested via real calls, while external services are mocked.
3.  **Scientific Rigor**: The plan explicitly distinguishes between *system logic validation* (can it run?) and *claim validation* (is it better?), avoiding circular reasoning.
4.  **Resource Constraints**: All library choices are pinned to CPU-compatible versions; memory usage is capped at a level consistent with the runner limit.

## Project Structure

### Documentation (this feature)

```text
specs/720-joyai-vl-interaction-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── joyai/
│   ├── __init__.py
│   ├── core/
│   │   ├── model_loader.py      # CPU-optimized model loading
│   │   ├── decision_engine.py   # Logic for silent/respond/delegate
│   │   └── video_processor.py   # Frame extraction and preprocessing
│   ├── services/
│   │   ├── asr_mock.py          # Mock ASR for pipeline testing
│   │   ├── tts_mock.py          # Mock TTS for pipeline testing
│   │   ├── agent_mock.py        # Mock background agent
│   │   ├── memory_mock.py       # Mock memory summarizer
│   │   └── viz_mock.py          # Mock visualization generator
│   ├── pipeline/
│   │   └── run_scenario.py      # End-to-end orchestration
│   └── utils/
│       ├── logger.py            # Decision logging (FR-008)
│       └── metrics.py           # Artifact collection
├── tests/
│   ├── unit/
│   │   ├── test_decision_engine.py
│   │   └── test_model_loader.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schema_validation.py
└── data/
    └── samples/                 # Minimal sample video frames (public domain)
```

**Structure Decision**: Single project structure (`src/joyai`) is selected to minimize overhead. Mock services are used to satisfy integration requirements (FR-005) without external dependencies, ensuring the pipeline runs within the 6-hour CI limit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mock Services (ASR/TTS/Memory/Viz/Agent) | Real services require external APIs or heavy local models that exceed RAM/CPU limits. | A fully integrated real-world pipeline would likely fail on a constrained runner with limited RAM and CPU resources due to resource contention and network latency. |
| Sampled Video Data | Processing full-length real-world videos exceeds the 2-hour processing window and RAM limits. | Full video processing would cause OOM errors or timeout the CI job. |
| CPU-Only Inference | The spec mandates CPU-only execution. | GPU acceleration is explicitly forbidden by the CI environment constraints. |

## Phases

### Phase 0: Environment & Dependency Verification (FR-001, FR-002)
*   **Goal**: Verify CI environment and install dependencies.
*   **Steps**:
    1.  Create `install/tests/verify_real_env.py` to check CPU cores, RAM, and GPU absence.
    2.  Create `install/install.sh` to install `torch` (CPU), `transformers`, `opencv-python-headless`.
    3.  Run verification script; assert exit code 0 and "GPU not available" message.
    4.  Log environment state to `logs/env_verification.log`.
*   **Success**: SC-001, SC-002 met.

### Phase 1: Core Model Execution & Decision Logic (FR-003, FR-004)
*   **Goal**: Execute VLM (CPU-optimized) on sample frames and validate decision artifacts.
*   **Steps**:
    1.  Load a CPU-compatible variant of the model (e.g., quantized 8B or distilled 1.3B if 8B OOMs).
    2.  Implement `video_processor.py` to extract frames from sample clips.
    3.  Implement `decision_engine.py` to parse model output and classify as "silent", "respond", or "delegate".
    4.  Run inference on multiple consecutive frames; log decision artifacts.
    5.  **Semantic Trigger Check**: Verify that "delegate" decisions contain reasoning keywords (e.g., "hard", "complex") and "silent" decisions contain "no trigger" or similar. This adds a layer of semantic consistency beyond trivial label checking.
    6.  **Triviality Check**: Verify that the model does not output the same decision label for all frames. If it does, flag as "Invalid Logic Fidelity".
    7.  **Fallback Validation**: If the 1.3B model is used (due to OOM), the `model_metadata` in the schema must reflect this. The validation logic will adjust thresholds accordingly (e.g., require higher confidence for "delegate" to ensure nuanced reasoning). The `data-model.md` includes a `deviation_flag` to track this.
    8.  Validate that "delegate" triggers the mock agent service.
*   **Success**: SC-003 met.

### Phase 2: End-to-End Integration & Pipeline (FR-005, FR-006, FR-007)
*   **Goal**: Integrate all components (ASR, Video, Model, TTS, Memory, Viz, Agent) and process a scenario.
*   **Steps**:
    1.  Implement `pipeline/run_scenario.py` to orchestrate ASR (mock), Video (sample), Model, TTS (mock), Memory (mock), Viz (mock), and Agent (mock).
    2.  **Explicit Invocation**:
        *   Call `memory_mock.py` to generate a `MemorySummaryArtifact` and verify its existence in `artifacts/`.
        *   Call `viz_mock.py` to generate a `VisualizationArtifact` and verify its existence in `artifacts/`.
    3.  Inject failure scenarios (e.g., mock ASR returns error) to test graceful degradation (FR-007).
    4.  Run complete pipeline on a recorded scenario (sample).
    5.  Measure total runtime; ensure < 2 hours.
    6.  Collect all artifacts (transcripts, audio files, logs, decisions, memory summaries, visualizations).
    7.  Validate `DelegationArtifact` against `contracts/delegation_artifact.schema.yaml`.
*   **Success**: SC-004, SC-005, SC-006 met.

### Phase 3: Logging, Validation & Reporting (FR-008, SC-007)
*   **Goal**: Validate artifacts against logic fidelity criteria (NOT human preference).
*   **Steps**:
    1.  Implement structured logging for all decisions (FR-008).
    2.  **Qualitative Validation Rubric (Deterministic)**: Generate a report using the following pre-defined, machine-readable criteria to avoid subjective bias:
        *   **Existence**: Did all components produce an artifact? (Pass/Fail)
        *   **Semantic Trigger**: Did the model's reasoning match the decision type (e.g., "delegate" -> "hard problem")? (Pass/Fail)
        *   **Consistency**: Did the pipeline handle errors without crashing? (Pass/Fail)
        *   **Triviality**: Did the model produce varied decisions? (Pass/Fail)
    3.  Generate a comparison report noting that "human preference" claims are **Unvalidated** in CI.
    4.  Validate that all decision paths are traceable in logs.
*   **Success**: SC-007 (reframed as Logic Fidelity) met.

## Risk Mitigation

*   **Risk**: 8B model exceeds 7 GB RAM on CPU.
    *   **Mitigation**: Use 4-bit quantization (`load_in_4bit`) if supported by CPU, or switch to a smaller distilled model (e.g., 1-3B) that approximates the behavior, documenting the deviation in `research.md` and `decision_artifact.schema.yaml`.
*   **Risk**: Inference time > 6 hours.
    *   **Mitigation**: Limit input to -10 frames per scenario; use `torch.no_grad()` and batch size 1.
*   **Risk**: External API dependencies for ASR/TTS.
    *   **Mitigation**: Use `mock` objects or lightweight local rule-based simulators for ASR/TTS during CI runs.

## Success Criteria Mapping

| Success Criteria | Measurement Source | Status in CI |
| :--- | :--- | :--- |
| SC-001: Environment Verification | `logs/env_verification.log` | Validated |
| SC-002: Dependency Installation | `install/install.sh` exit code | Validated |
| SC-003: Model Artifact Production | `artifacts/decisions.json` | Validated |
| SC-004: Pipeline Completion Time | `logs/pipeline.log` (timestamp diff) | Validated |
| SC-005: Component Integration | Artifact existence check | Validated |
| SC-006: Error Handling | Error injection test results | Validated |
| SC-007: Decision Logging / Logic Fidelity | `logs/decision.log` + Rubric | Validated (Logic Fidelity only) |
| SC-007: Human Preference Superiority | N/A | **Unvalidated** (Requires Human Study) |

## Constitution Check (Detailed)

*   **Principle I (SSoT)**: Adhered to by using `spec.md` as the source of truth. All deviations are documented.
*   **Principle V (Real-Call Testing)**: Adhered to by performing real model inference and mocking only external/heavy dependencies.
*   **Missing Constitution**: As no `constitution.md` was provided, this plan defaults to standard scientific rigor and resource constraints as defined in the project's `spec.md`.