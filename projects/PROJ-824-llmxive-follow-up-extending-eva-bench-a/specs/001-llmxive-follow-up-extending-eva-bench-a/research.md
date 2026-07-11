# Research: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

## 1. Research Question & Hypothesis

**Primary Question**: At what point of injected network latency (200ms–2000ms) does the "Conversation Progression" metric in EVA-Bench exhibit a non-linear collapse (inflection point), and is this degradation profile distinct from the known acoustic noise degradation?

**Hypothesis**: There exists a specific latency threshold (hypothesized ~800ms) where the score drops precipitously. This threshold represents a distinct failure mode from acoustic noise, as temporal disruption affects turn-taking logic differently than signal quality.

## 2. Dataset Strategy

**Primary Dataset**: EVA-Bench (ServiceNow-AI/eva-bench)
- **Source**: Verified HuggingFace Dataset.
- **URL**: `
- **Format**: JSONL containing audio file paths (or base64) and scenario metadata.
- **Relevance**: Contains the specific "Turn-Taking" and "Conversation Progression" metrics required for the study.
- **Variable Fit & Verification**:
 1. **Audio Availability**: We will first verify that the dataset contains actual audio files (not just transcripts). If the dataset only provides transcripts, the plan will fail fast with a clear error code or switch to a TTS fallback (if permitted by the spec) to generate synthetic audio for injection.
 2. **Turn Metadata**: The dataset must provide `turns` with `start_time` and `end_time` to ensure precise injection boundaries.

**Baseline Data (Acoustic Noise)**:
- **Source**: Re-run of the original EVA-Bench pipeline with acoustic perturbations.
- **Strategy**: To satisfy FR-005 and ensure a valid within-subjects design, we will re-run the acoustic perturbation on the **exact same subset** of scenarios used for the latency sweep.
- **Constraint**: If the original pipeline is LLM-heavy, we will use a **distilled surrogate model** or a **rule-based approximation** for the acoustic sweep to ensure CPU feasibility (FR-007). We will not rely on published curves alone.

## 3. Methodology

### 3.1 Latency Injection (FR-001, SC-001)
- **Tool**: `pydub` (preferred for simplicity) or `scipy.signal`.
- **Process**:
 1. Load audio file.
 2. **Turn Boundary Validation**: Identify turn boundaries using the `turns` metadata from JSONL. **Strict Rule**: Inject silence **only** at the `end_time` of a user turn and `start_time` of the agent turn. If metadata is missing or ambiguous, the script will fail fast rather than guess (preventing misalignment).
 3. Insert silence segment of duration $D \in \{200, 400, \dots, 2000\}$ ms.
 4. Save as new file (e.g., `scenario_001_delay_800ms.wav`).
- **Validation**: Verify file duration increases by exactly $D$ ms and original audio samples are unchanged.
- **Metric Definition Verification**: We will verify that the "Turn-Taking" metric in EVA-Bench is not tautologically defined by silence thresholds (e.g., "penalty for silence > X ms"). If it is, we will prioritize 'Interruption Count' or 'Semantic Coherence' (FR-009).

### 3.2 Evaluation Pipeline (FR-002)
- **Execution**: Invoke the EVA-Bench scoring function on the modified audio.
- **Output**: JSON/CSV with `scenario_id`, `latency_ms`, `turn_taking_score`, `conversation_progression_score`.
- **Constraint**: Must run on CPU. If the original pipeline uses heavy LLMs for scoring, we will use a **sampled subset** of scenarios (e.g., 50 scenarios) for the full sweep if the full run exceeds 6 hours, or rely on a lightweight scoring surrogate. *Assumption*: The scoring logic is CPU-tractable or can be approximated.

### 3.3 Statistical Analysis (FR-003, FR-004, SC-002, SC-005)
- **Repeated-Measures ANOVA**: To test if latency condition significantly affects scores (within-subjects design).
- **Piecewise Regression**: Fit a segmented linear model to `Conversation Progression` vs. `Latency`.
 - Model: $Y = \beta_0 + \beta_1 X + \beta_2 (X - \tau)_+ + \epsilon$
 - Where $\tau$ is the breakpoint (threshold).
 - Method: Grid search for $\tau$ (200–2000ms) or use `segmented` package in Python (if available) or custom implementation.
- **Sensitivity Analysis (SC-005)**: Sweep the identified breakpoint $\tau$ over a range of $\pm 50$ ms. Recalculate the model fit for each sweep point to verify that the inflection point is stable and not an artifact of noise. Report the stability range.

### 3.4 Comparative Analysis (FR-005, FR-008, SC-003)
- **Normalization**: Since the x-axes (Time vs. SNR) are different, we will normalize both curves to a **0-1 Severity Scale** (0 = no degradation, 1 = max degradation observed) before comparing Areas Under the Curve (AUC).
- **Metric**: Compare AUC(Latency) vs. AUC(Acoustic) on the normalized scale.
- **Interaction Test**: Two-way ANOVA (Factor 1: Condition Type [Latency/Acoustic], Factor 2: Severity Level) to check for significant interaction (distinct failure modes).
- **Within-Subjects**: Ensure the same subset of scenarios is used for both conditions to satisfy the ANOVA assumption.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
 - **Streaming**: Process audio files one by one or in small batches to stay under 7GB RAM.
 - **No GPU**: Explicitly avoid `torch.cuda`. Use `scipy` and `numpy` which are CPU-native.
 - **Power Analysis**: Before the full run, we will perform a power analysis to determine the minimum N required to detect the hypothesized effect size. If N=50 is insufficient, we will report the study as "Pilot" with low power or increase the sample size if time permits.
 - **Time Limit**: 6 hours.
 - Estimated time per scenario (10 latency steps) = $T$.
 - Total time = $N \times 10 \times T$.
 - If $T > 10$ seconds, we will default to the power-calculated sample size (or a representative sample of 50 scenarios) to ensure the CI job passes.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Download Fails** | Blocker | Retry logic with exponential backoff; fail fast with clear error code. |
| **Scoring Pipeline Too Slow** | Timeout (>6h) | Implement scenario sampling (e.g., 50 scenarios) and report as "Pilot Study" if full run fails. |
| **Regression Fails to Converge** | Invalid Threshold | Fall back to linear regression and report "No distinct threshold detected" with confidence intervals (Edge Case). |
| **Audio Format Mismatch** | Runtime Error | Validate audio format before injection; convert to WAV 16kHz if needed. |
| **Metric Tautology** | Invalid Conclusion | Verify metric definitions; switch to 'Interruption Count' if 'Turn-Taking' is silence-based. |

## 6. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use `pydub` for injection** | Simpler API for silence insertion than `scipy` raw buffers; standard CPU library. |
| **Sample scenarios if needed** | Ensures compliance with SC-004 (6h limit) while maintaining statistical validity via power analysis (or acknowledging power limits). |
| **Acoustic Baseline Strategy** | Re-run on same subset with lightweight surrogate to satisfy FR-005 and ensure valid within-subjects ANOVA. |
| **Normalized AUC** | Required to compare Time (ms) vs. SNR (dB) curves validly. |