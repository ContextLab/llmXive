# Research: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

## Problem Statement

The original ResearchClawBench study identified "experimental protocol mismatch" as a critical failure mode in autonomous scientific agents. This follow-up study investigates whether injecting domain-specific procedural scaffolds (static templates from laboratory manuals) can improve protocol adherence without compromising the agent's ability to generate valid scientific hypotheses (Scientific Core). The core hypothesis is that scaffolding improves procedural alignment (measurable via paired tests) while maintaining scientific core scores within a non-inferiority margin (measurable via TOST).

**Critical Note on Power**: With N=10 (or N=30 with 3 generations per task), the study is underpowered to detect moderate effect sizes (Power < 0.4). Non-significant results for "Scientific Core" are interpreted strictly as "inconclusive" regarding safety, not as validation. The primary claim is the *feasibility of the decoupling method*, not a definitive proof of efficacy.

## Dataset Strategy

**Dataset**: ResearchClawBench
**Source Status**: NO verified URL found. The dataset is referenced by name only.
**Access Method**: The dataset **must** be provided as a local artifact in `data/raw/` with a known checksum. The `data_loader` will validate the checksum against the expected hash. If the checksum does not match, the system aborts (FR-006). This satisfies the 'Reproducibility' principle via local artifact integrity verification.
**Selection Criteria**:
- Filter for tasks where the dominant failure mode is "experimental protocol mismatch".
- Select a subset of tasks.
- Verify metadata contains the required flag (FR-006).

**Variable Fit**:
- **Required**: Task description, hidden target paper, failure mode metadata.
- **Required**: Scoring rubric (`rubric_schema.json`) defining "Protocol Alignment" (0-50) and "Scientific Core".
- **Verification**: The `data_loader` will assert the presence of the "protocol mismatch" flag. If the dataset lacks this metadata, the system aborts (FR-006).

**Data Hygiene**:
- Raw data will be checksummed upon ingestion.
- The filtered subset of 10 tasks will be saved as `data/processed/selected_tasks.csv` with a derivation log.

## Methodology

### Experimental Design
- **Design**: Within-subjects (Paired) design.
- **Conditions**:
  1. **Zero-Shot**: Agent receives task description only.
  2. **Scaffolded**: Agent receives task description + injected domain-specific protocol template (from `assets/templates/`).
- **Agents**: A set of distinct autonomous agents from the original study. **CPU-Compatibility Check**: Before execution, each agent will be validated for CPU compatibility (RAM < 7GB, no GPU requirement). If an agent fails, it is substituted with a 'CPU-Optimized Variant' (e.g., quantized model) or excluded, and N is reduced.
- **Tasks**: 10 specific tasks flagged for protocol mismatch.
- **Variance Control**: For each task/condition, the system will run **3 independent generations** (Total N=30 pairs) to average out LLM generation noise. If 3 generations exceed the 6-hour timeout, the system falls back to 1 generation and reports reduced power.
- **Total Runs**: 140 (7 agents × 2 conditions × 10 tasks) * 3 generations = 420 runs (if feasible).

### Execution Constraints
- **Platform**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
- **Timeout**: 6 hours per run.
- **Concurrency**: Max 7 concurrent runs.
- **Wall-Clock Budget**: 24 hours.

### Scoring Logic
- **Rubric**: `rubric_schema.json` defines the scoring logic.
- **Metrics**:
  - **Protocol Alignment (0-50)**: Measures adherence to procedural steps.
  - **Scientific Core**: Measures validity of hypothesis generation and reasoning.
- **Rubric Orthogonality Validation (FR-008 Expanded)**: Before main runs, the system will score dummy outputs:
  - Set A: Contains scaffold text but fails steps → Expected Low Score.
  - Set B: Contains steps but no scaffold text → Expected High Score.
  - **Prompt Content Analysis**: The scaffold text will be analyzed to ensure it contains **no scientific reasoning cues** (e.g., no hypothesis suggestions, no domain-specific theories). This ensures the 'Scientific Core' score is not biased by the prompt structure.
  - **Inter-Rater Reliability (IRR) Pilot**: A pilot study will be conducted to estimate the standard error of the 'Scientific Core' metric. The TOST margin of 5 points is defined as a **conservative assumption**. If the pilot IRR > 5, the TOST test is marked "inconclusive" rather than forced.

### Statistical Analysis Plan

1. **Data Preparation**:
   - Aggregate scores into a paired dataset (Zero-Shot vs. Scaffolded) for each task/agent pair.
   - Exclude runs with timeouts or scaffold conflicts (FR-007).
   - Average the 3 generations per task/condition to create a single score pair per task/agent.

2. **Protocol Alignment Analysis**:
   - **Test Selection**: **Pre-specified Wilcoxon signed-rank test** (or permutation test) due to low power of normality tests at N=10. Shapiro-Wilk is **not** used for test selection.
   - **Output**: p-value, test statistic, effect size (Cohen's d or r), 95% CI.
   - **Hypothesis**: Scaffolded > Zero-Shot.

3. **Scientific Core Analysis (Safety Bound)**:
   - **Test**: Two One-Sided Tests (TOST) for equivalence.
   - **Margin**: 5 points (conservative assumption pending pilot validation).
   - **Hypothesis**: The difference between conditions is within [-5, +5].
   - **Interpretation**:
     - Both p-values < 0.05 AND Pilot IRR ≤ 5 → "Safe" (Equivalence established).
     - Otherwise → "Inconclusive" (Cannot rule out degradation or margin too tight).
   - **Power Acknowledgement**: Explicitly report that N=10 (or N=30) yields low power (<0.4) for moderate effects. Non-significant results are treated as inconclusive, not validated.

4. **Failure Mode Audit**:
   - If the 10 selected tasks do not have "protocol mismatch" as the dominant mode, generate `results/failure_mode_audit.csv` and abort or flag as per FR-006/Edge Cases.

5. **Scaffold Conflict Detection**:
   - Validate task metadata against `constraint_keywords` in template schema.
   - Log "Scaffold Conflict" warning if detected.
   - Exclude from primary analysis; record ID for human audit.

## Decision Rationale (Compute Feasibility)

- **No GPU**: The plan uses lightweight Python libraries (`scipy`, `pandas`) and runs pre-trained agents. **CPU-Compatibility Check** ensures agents are viable. If an agent requires GPU, it is substituted or excluded.
- **Memory**: Data is streamed and aggregated in small batches. The statistical analysis operates on a tiny dataframe (<1KB).
- **Runtime**: The 6-hour timeout per run is the bottleneck. The plan assumes agents are optimized for CPU. If an agent exceeds the timeout, it is logged and excluded (Edge Case handling).
- **Statistical Methods**: Wilcoxon and TOST are computationally trivial on N=30.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset lacks "protocol mismatch" flag | Fatal (FR-006) | System aborts with clear error; no partial results. |
| Agent runtime > 6 hours | Data loss | Timeout handling logs exclusion; results reported with N reduction. |
| Low statistical power (N=10) | Inconclusive results | Explicitly report power limitations; interpret "non-significant" as "inconclusive" not "safe". |
| Scaffold conflicts | Bias | Detection logic excludes conflicting runs; logs for human audit. |
| Rubric scores scaffold text | Invalid metric | FR-008 validation + Prompt Content Analysis ensures rubric scores steps, not text. |
| Margin (5 points) too tight | False "Inconclusive" | Margin is a conservative assumption; pilot IRR validation will confirm feasibility. |
| Agent not CPU-compatible | Fatal | CPU-Compatibility Check substitutes or excludes agent; reports N reduction. |


## projects/PROJ-957-llmxive-follow-up-extending-researchclaw/specs/001-llmxive-follow-up-extending-researchclaw/data-model.md