# Research: Dynamic Socio-Cognitive State Injection

## Overview

This research phase validates the feasibility of the proposed methodology, confirms dataset generation, and defines the statistical strategy for the `001-dynamic-state-injection` feature. The core hypothesis is that **dynamic injection of socio‑cognitive states, inferred from turn‑level dialogue, improves consensus gap closure** in high‑emotion, culturally diverse conflict scenarios compared to a static baseline.

## Dataset Strategy

### Generated Data – SoCRATES Pipeline
The SoCRATES pipeline is a **local generator** (not a pre‑packaged dataset). Running `code/data/generator.py` creates synthetic conflict trajectories that contain all required variables:

| Variable | Description |
|----------|-------------|
| `emotional_reactivity` | Float 0.0–10.0 (ground‑truth score). |
| `cultural_identity` | List of categorical tags (e.g., `["Western","Eastern"]`). |
| `dialogue_history` | Ordered list of speaker turns (text). |
| `ideal_resolution` | Textual ground‑truth resolution used by the evaluator. |

Because the data are generated on‑the‑fly, we guarantee **dataset‑variable fit** (SC‑002) and avoid reliance on external sources.

### No External Fallback Dataset
All required metadata for oversampling and classifier training are produced by the generator. Consequently, the previously mentioned “UCI Conflict Resolution” dataset has been removed from the plan to eliminate invalid references.

## Methodology

### 1. Data Generation (US‑1, FR‑001)
- **Process**: Invoke the SoCRATES generator to synthesize **500 trajectories**.
- **Oversampling**: The generator is configured to ensure **≥40 %** of trajectories have either `emotional_reactivity > 7.0` **or** a non‑dominant `cultural_identity` tag.
- **Verification**: A JSON summary (`data/processed/summary.json`) is emitted with category counts; the script aborts if the 40 % threshold is not met.

### 2. Dynamic State Classifier (FR‑002)
- **Features**: For each inference step (every 3 turns) we extract:
  1. **Turn‑level text features** – bag‑of‑words TF‑IDF vectors from the last three dialogue turns.
  2. **Auxiliary metadata** – scenario `conflict_type`, `emotional_reactivity`, and `cultural_identity` (treated as categorical encodings).
- **Labels**: State labels (`escalating`, `cultural‑friction`, `neutral`, `de‑escalating`) are **automatically annotated** on the generated trajectories using heuristic rules (sentiment spikes, presence of conflict‑specific keywords). This yields a training set where labels are derived from the dialogue itself, satisfying the “dynamic inference” requirement.
- **Model**: Logistic Regression (`scikit‑learn`) with L2 regularization; training runs on CPU and produces a pickled model (`data/models/classifier.pkl`).
- **Confidence Handling**: If the predicted probability for the top label is `< 0.6`, the system defaults to the `neutral` state, ensuring a safe fallback.

### 3. Experimental Execution (US‑2, FR‑003, FR‑004)
- **Conditions**:
  - **Static** – Fixed system prompt throughout the trajectory.
  - **Adapter** – At each 3‑turn interval, the classifier predicts a state; the corresponding instruction (e.g., “Validate cultural norms”, “De‑escalate”) is **injected** into the system prompt for the next turn.
- **LLMs**: Eight CPU‑compatible models (e.g., `Llama‑3‑8B‑GGUF`, `Mistral‑7B‑GGUF`, `Gemma‑7B‑GGUF`). Models exceeding 7 GB RAM are excluded per Assumption 2.
- **Ordering**: Data generation → classifier training → paired experiments → evaluation → statistical analysis.

### 4. Consensus Gap Metric (FR‑005)
`Consensus Gap Closure = 1 - (distance(LLM_output, ideal_resolution) / max_distance)`, where `distance` is a token‑level edit‑distance normalized to `[0,1]`. The `ideal_resolution` is generated **independently** of the state labels; it reflects the optimal resolution defined by the SoCRATES pipeline, ensuring no leakage between predictor and outcome.

### 5. Statistical Analysis (FR‑006, FR‑007)
- **Normality**: Shapiro‑Wilk test on paired differences (Adapter − Static) per LLM.
- **Test Selection**:
  - If `p > 0.05` → Paired t‑test (report Cohen’s d).
  - Else → Wilcoxon signed‑rank test (report rank‑biserial correlation).
- **Multiple‑Comparison Correction**: Holm‑Bonferroni applied across the eight LLMs to control family‑wise error (FR‑007).
- **Effect‑size Reporting**: Both `p_value` and `effect_size` are included in the JSON report; `is_significant` flags `p < 0.05`.

## Decision Rationale

- **Dynamic Text‑Based Classifier**: Logistic Regression on turn‑level text satisfies FR‑002’s requirement for a lightweight, CPU‑only model while truly inferring state from dialogue dynamics rather than static metadata.
- **Paired Design**: Controls for trajectory‑level variance, isolating the injection variable per Constitution Principle VII.
- **Holm‑Bonferroni**: Balances Type I error control with statistical power across multiple LLM comparisons.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Generated data lack sufficient variability | Medium | Verify distribution after generation; regenerate with adjusted seeds if needed. |
| Classifier confidence low on many turns | Medium | Use neutral fallback; log fallback frequency for sensitivity analysis (SC‑005). |
| Model RAM exceeds limit | High | Pre‑screen model sizes; automatically skip oversized models and record exclusion. |
| Runtime > 6 h | Critical | Limit trajectories to 500; batch inference; early‑stop if wall‑clock exceeds 5 h (allowing margin). |
