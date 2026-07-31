# Research Draft: Dynamic Socio-Cognitive State Injection in LLM Mediation

## Abstract
This study evaluates the efficacy of dynamic socio-cognitive state injection in Large Language Models (LLMs) for conflict mediation. We compare a dynamic adapter condition against a static baseline across multiple model architectures.

## 1. Introduction
Conflict resolution in digital environments often lacks the nuanced adaptability of human mediators. This research investigates whether injecting real-time socio-cognitive states (e.g., "de-escalate", "validate cultural norms") improves consensus gap closure.

## 2. Methods

### 2.1 Experimental Design
We employed a within-subjects design where each conflict trajectory was processed under two conditions:
1. **Static Baseline**: Standard prompt with no state injection.
2. **Dynamic Adapter**: Real-time injection of socio-cognitive states derived from a lightweight classifier.

### 2.2 Data Generation
Synthetic conflict trajectories were generated using the SoCRATES pipeline, oversampling for high emotional reactivity and diverse cultural identity attributes to ensure robustness.

### 2.3 Model Selection and Exclusion Criteria
To ensure reproducibility within CPU-only constraints (FR-004), we implemented strict memory profiling.

**Exclusion Logic (T009 & T041):**
Models were pre-screened using an estimated RAM usage check. Any model with an estimated memory footprint exceeding 7GB was excluded from the experiment suite. This exclusion is recorded in `data/results/scope_adjustments.json`.

Specifically:
- **T009 (Model Loader):** A pre-flight check estimates model size. If `estimated_ram_gb > 7`, the model is skipped and logged.
- **T041 (Memory Profiler):** During runtime, memory usage is instrumented. If a model exceeds the threshold, it is dynamically excluded, and the exclusion is propagated to the statistical analysis to prevent bias.

Only models passing these criteria were included in the final statistical family (N_actual).

### 2.4 Procedure
Trajectories were processed turn-by-turn. A logistic regression classifier determined the socio-cognitive state every N=3 turns. If confidence was low, a "neutral-monitoring" state was injected.

## 3. Results

### 3.1 Statistical Analysis
Consensus gap closure was calculated for all valid trajectories. A paired t-test (or Wilcoxon signed-rank if non-normal) was performed between conditions. Holm-Bonferroni correction was applied to the set of *actually executed* LLMs.

### 3.2 Power Analysis
The study was powered to detect a medium effect size (Cohen's d = 0.5). A formal power analysis report (T049) was generated prior to execution.

## 4. Discussion
The results indicate whether dynamic state injection provides a statistically significant advantage over static prompting in conflict resolution scenarios.

## 5. Conclusion
Future work will explore GPU-accelerated architectures to reduce latency while maintaining the exclusion criteria established in this study.
