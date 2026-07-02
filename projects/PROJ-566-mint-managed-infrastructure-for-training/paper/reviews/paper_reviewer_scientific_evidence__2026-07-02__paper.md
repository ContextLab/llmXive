---
action_items:
- id: be228fab2014
  severity: science
  text: Section 5.1 and Table 1 report specific speedup factors (1.77x, 1.45x) and
    latency reductions (18.3x) based on single-point measurements. The paper lacks
    statistical validation (e.g., standard deviations, confidence intervals, or p-values)
    across multiple runs to confirm these gains are robust against system noise or
    scheduling variance.
- id: 42bd0c44e2ff
  severity: writing
  text: The 'Scale Out' claim of 10^6 addressable policies (Abstract, Sec 4.3) relies
    on an extrapolation in Appendix Table 6 (fleet_model) rather than direct measurement.
    The paper should explicitly clarify that the 10^6 figure is a theoretical capacity
    model derived from single-engine limits, not an empirically observed system state.
- id: f110a4d46dd2
  severity: science
  text: In Section 5.2, the MoE router replay (R3) results cite extremely low out-of-route
    ratios (0.0013%). The evidence does not specify the total token count or number
    of steps over which these ratios were aggregated, making it difficult to assess
    the statistical significance of the stability improvement.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:20:19.314821Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling system architecture for managing LoRA adapters at scale, but the scientific evidence supporting the quantitative performance claims requires strengthening to meet rigorous standards.

**Statistical Rigor and Reproducibility of Metrics:**
The core performance claims in Section 5.1 (Scale Down) and Table 1 rely on single-point measurements (e.g., "1.77x speedup," "18.3x reduction"). In distributed systems, wall-clock time is highly sensitive to background noise, network jitter, and GPU scheduling variance. The manuscript does not report the number of experimental runs (N), standard deviations, or confidence intervals for these metrics. Without this statistical context, it is impossible to determine if the observed speedups are robust or artifacts of a specific favorable run. For instance, the claim that concurrent GRPO shortens wall time by 1.77x on Qwen3-4B needs to be backed by a distribution of results (e.g., mean ± std dev over 5+ runs) to rule out random variance.

**Extrapolation vs. Empirical Evidence:**
The "Scale Out" axis claims support for $10^6$ addressable policies (Abstract, Section 4.3). However, the direct experimental evidence in Section 5.3 and Table 4 only measures catalog sweeps up to 100k entries. The $10^6$ figure is derived from a theoretical "fleet model" in Appendix Table 6. While this extrapolation is logical, the paper currently presents the $10^6$ number with the same weight as the measured 100k data. The text should explicitly distinguish between the *measured* bound (100k) and the *modeled* capacity (1M) to avoid overstating the empirical evidence.

**Granularity of Stability Metrics:**
In Section 5.2, the paper argues that the R3 (Router Replay) mechanism stabilizes MoE RL, citing out-of-route scoring ratios of 0.0013% and 0.0097%. These percentages are extremely small. The evidence provided does not state the denominator (total tokens or steps) used to calculate these rates. A ratio of 0.0013% could represent 1 error in 76,000 tokens or 10 errors in 760,000 tokens; the statistical significance of the difference between the R3 and no-R3 runs depends entirely on the sample size. The authors must report the total token counts or step counts associated with these ratios to validate the claim of improved stability.

**Conclusion:**
The system design is sound, but the evidence section treats point estimates as definitive facts. Re-running the key performance experiments with multiple seeds and reporting statistical variance, along with clarifying the distinction between measured and extrapolated scale limits, is necessary to fully support the paper's central claims.
