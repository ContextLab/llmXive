---
action_items:
- id: ca51964f5ea2
  severity: science
  text: Clarify the generalization scope of the Sim-to-Real gain (95.1% on 59 tasks).
    The 189 Stable-fail tasks were not run on real devices; explicitly state if the
    95.1% figure applies only to the signal subset or is extrapolated.
- id: 3ef1974d612c
  severity: science
  text: Report variance across training seeds for the GRPO study. The +12.8pt gain
    is from a single 10-step run; multiple seeds would strengthen the evidence for
    online RL efficacy.
- id: a381d78d1192
  severity: science
  text: Discuss potential bias in VLM judge errors (10.2% misjudgment). If errors
    are non-random (e.g., higher on hard tasks), the real-device SR estimates may
    be biased.
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T00:54:33.855736Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This paper presents strong scientific evidence for the core claims regarding platform efficiency and benchmark design, but the Sim-to-Real transfer study requires additional clarification on generalizability and statistical robustness.

**Strengths:**
1. **Benchmark Scale:** The 416 task templates (256 test) provide a substantial sample size for evaluating mobile GUI agents, exceeding most prior work (Table 1).
2. **Deterministic Verification:** The use of structured JSON state for judging (§4.2) eliminates the ambiguity of VLM-based or heuristic-based judging for simulation tasks, providing high-fidelity ground truth.
3. **Efficiency Claims:** The memory (400 MB) and startup time (3 s) metrics are concrete and compared against specific baselines (Table 1, Appendix I).

**Concerns:**
1. **Sim-to-Real Sample Bias:** The real-device evaluation (§5.2) focuses on a "signal-bucket subset" of 59 tasks selected because the simulation showed training gains (Uplift, Stable-pass, Mid). The 189 "Stable-fail" tasks (where simulation showed no gain) were mostly not tested on real devices (only 15 sampled). While the authors frame this as an "existence proof," the headline claim of "95.1% retained gain" could be misinterpreted as applying to the full 256-task distribution. The evidence supports transfer *for tasks where simulation training works*, but does not evidence transfer for tasks where it fails.
2. **Training Variance:** The GRPO training study reports a single run (+12.8 pt gain, §5.2). Online RL performance is often sensitive to seeds and hyperparameters. Without multiple training seeds, the robustness of the +12.8 pt improvement is unclear. The inference trials have reported std dev (e.g., $\pm$1.4), but the training gain does not.
3. **VLM Judge Error:** The real-device ground truth relies on VLM judges (Qwen3.6-Plus, GPT-5.4) with a reported 10.2% misjudgment rate (Appendix G). While audited, if these errors correlate with task difficulty or model performance (e.g., harder trajectories are harder to judge), the reported real-device SR could be biased. The sensitivity analysis in Appendix G shows consistent error rates across judges but does not rule out systematic bias.

**Recommendations:**
- Explicitly qualify the "95.1% retained gain" as specific to the 59-task signal subset in the abstract and conclusion.
- Add at least 2-3 training seeds to the GRPO experiment to report variance on the +12.8 pt gain.
- In the discussion, acknowledge that the 189 Stable-fail tasks remaining untested on real devices limits the claim of general Sim-to-Real robustness.
