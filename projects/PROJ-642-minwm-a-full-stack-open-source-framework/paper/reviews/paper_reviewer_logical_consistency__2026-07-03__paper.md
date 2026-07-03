---
action_items:
- id: 646b04237911
  severity: science
  text: In Sec 3.2 (Stage 3), Eq 4 minimizes KL to p_data, but text claims alignment
    with the 'bidirectional teacher'. Clarify if s_real approximates p_data or the
    teacher's distribution to resolve the logical conflict in the training signal
    source.
- id: 95336d949b2c
  severity: writing
  text: Table 1 compares total bidirectional generation time against AR first-frame
    time. This 'total vs. partial' comparison logically inflates the speedup metric.
    Clarify if the baseline should be bidirectional first-frame latency for a fair
    interactivity comparison.
- id: e81fddd6278b
  severity: science
  text: Sec 4.3 claims WorldPlay-generated trajectories are 'effectively ground-truth'
    while SpatialVid estimates are noisy. Logically justify why a generative model's
    conditioned output is superior to perception estimates, as both are synthetic/non-physical.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:43:45.969185Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent pipeline for converting bidirectional diffusion models into autoregressive world models. However, there are logical gaps in the justification of the distillation objective and the interpretation of latency metrics.

First, in Section 3.2 (Stage 3: asymmetric DMD), the authors state the goal is to align the few-step AR model with the "high-quality distribution of the bidirectional teacher." Yet, Equation 4 defines the objective as minimizing the KL divergence between the student's distribution $p_{\theta,t}$ and $p_{\text{data},t}$, estimated by a frozen model $s_{\text{real}}$. If $s_{\text{real}}$ is initialized from the bidirectional teacher, it approximates the teacher's distribution, not the true data distribution. The text conflates "data distribution" with "teacher distribution" without clarifying if the teacher is assumed to be a perfect proxy for data. If the teacher is imperfect, optimizing against it directly (as implied by the text) contradicts the standard DMD formulation which targets the data distribution. This ambiguity weakens the logical support for the claimed "asymmetric" advantage.

Second, the latency analysis in Section 4.2 and Table 1 relies on a definition of "first-frame latency" that creates a logical asymmetry in comparison. The bidirectional baseline latency (e.g., 771s for HY1.5) represents the time to generate the *entire* 77-frame video. The AR baseline latency (e.g., 3.4s) represents the time to generate only the *first* frame (or chunk). While the text acknowledges this difference, presenting a 223x speedup as a measure of "real-time interactive" capability is logically misleading. A fair comparison for interactivity would be the time to generate the first frame of the bidirectional model (which might be near zero if streaming is supported, or the full time if not) versus the AR model's first frame. The current metric compares "total work" vs. "partial work," inflating the perceived speedup.

Finally, the ablation on training data (Section 4.3) posits that SpatialVid fails due to noisy estimated poses, while WorldPlay-generated data succeeds. The logical leap here is assuming that WorldPlay's generated videos provide "effectively ground-truth trajectories." WorldPlay generates videos *conditioned* on trajectories; it does not measure them. If the WorldPlay model has its own biases or errors in following the trajectory, the "ground truth" is just as synthetic as the SpatialVid estimates. The paper does not logically justify why a generative model's adherence to a prompt is superior to a perception model's estimation of a real video, other than an implicit assumption that the generative model is more consistent. This requires a clearer logical argument or empirical validation of the trajectory fidelity.
