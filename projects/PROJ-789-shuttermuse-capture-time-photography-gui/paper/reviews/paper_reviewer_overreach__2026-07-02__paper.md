---
action_items:
- id: ed4b2d24fe37
  severity: writing
  text: The paper makes several strong claims regarding the performance and capabilities
    of ShutterMuse that slightly exceed the evidence provided in the results tables.
    First, the Abstract and Introduction repeatedly claim that ShutterMuse achieves
    the "best overall photographer-side performance among evaluated baselines." While
    ShutterMuse leads in IoU, BDE, and Refinement Success Rate (R), Table 1 clearly
    demonstrates that it does not outperform all baselines on every metric. Specifically,
    Qwen3-VL-3
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:15:57.452834Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the performance and capabilities of ShutterMuse that slightly exceed the evidence provided in the results tables.

First, the Abstract and Introduction repeatedly claim that ShutterMuse achieves the "best overall photographer-side performance among evaluated baselines." While ShutterMuse leads in IoU, BDE, and Refinement Success Rate (R), Table 1 clearly demonstrates that it does not outperform all baselines on every metric. Specifically, Qwen3-VL-32B achieves a Keep Success Rate (KSR) of 98.18%, significantly higher than ShutterMuse's 74.55%. Similarly, Gemini-3.0-Pro achieves a higher Reject Success Rate (RSR) of 82.76% (tied with ShutterMuse) but a higher KSR. The claim of "best overall" implies a dominance that is not present in the data. The authors should refine this claim to "best overall balance" or explicitly state that it leads in refinement accuracy while maintaining competitive decision-making, rather than implying a blanket superiority.

Second, the claim of "competitive subject-side pose recommendation" in the Abstract and Introduction is somewhat generous given the quantitative results in Table 2. ShutterMuse achieves a mean score of 0.34, which is lower than both Nano-Banana-Pro (0.39) and GPT-Image-2 (0.35). While the inference time is substantially lower (4.96s vs 55.16s/102.61s), the quality gap is noticeable. The text currently frames this as "competitive," which might mislead readers into thinking the quality is on par. A more accurate characterization would be that it "approaches the performance of larger foundation models with significantly lower inference cost" or "offers a favorable trade-off between quality and efficiency."

Finally, the User Study section concludes that the MLLM-based evaluation "aligns well with human judgments." This conclusion is drawn from a study involving only six participants and 100 samples per subset. While the reported Spearman's rank correlation coefficient (SRCC) of 0.90 is high, extrapolating this to a general alignment with "human judgments" across the broad domain of photography is an overreach. The conclusion should be more conservative, acknowledging the limited scale of the user study and framing the alignment as observed within the specific experimental context.

These issues are primarily matters of precise wording and calibration of claims to the data, rather than fundamental flaws in the methodology.
