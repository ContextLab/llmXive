---
action_items:
- id: ec86c4363a24
  severity: writing
  text: The paper makes several strong claims regarding the superiority of ShutterMuse
    and the limitations of existing methods that require qualification to avoid overreach.
    First, the Abstract and Introduction claim that ShutterMuse achieves the "best
    overall photographer-side performance among evaluated baselines." While Table
    1 shows ShutterMuse leads in IoU, BDE, R, RSR, and MLLM-Score, it does not achieve
    the highest Keep Success Rate (KSR), where Qwen3-VL-32B-Instruct scores 98.18%
    compared to Shu
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T22:05:43.670245Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the superiority of ShutterMuse and the limitations of existing methods that require qualification to avoid overreach.

First, the Abstract and Introduction claim that ShutterMuse achieves the "best overall photographer-side performance among evaluated baselines." While Table 1 shows ShutterMuse leads in IoU, BDE, R, RSR, and MLLM-Score, it does not achieve the highest Keep Success Rate (KSR), where Qwen3-VL-32B-Instruct scores 98.18% compared to ShutterMuse's 74.55%. The term "best overall" is slightly misleading without qualification. The authors should clarify that ShutterMuse offers the best *balanced* performance across refinement and decision-making tasks, rather than an absolute best across all metrics.

Second, the claim of "substantially lower inference cost" for subject-side guidance (Abstract, Section 4.2) relies on a comparison with image-editing foundation models (Nano-Banana-Pro, GPT-Image-2) that perform full image generation/editing. While the 10x speedup is significant, the comparison is against models with a much heavier computational burden than a pure pose recommendation task would typically entail. The paper does not compare against a lightweight pose estimator baseline to isolate the cost of the "guidance" reasoning. The text should explicitly state that the efficiency gain is relative to *generative* baselines to prevent readers from inferring that the model is more efficient than all possible pose estimation approaches.

Finally, the assertion that existing general-purpose MLLMs and specialized models "neither provides actionable pose guidance" (Abstract, Introduction) overstates the limitations of prior art. The paper notes in Section 4.2 that general MLLMs failed to produce valid outputs under the specific "validity check" of the evaluation protocol. This suggests a failure in the *prompting strategy* or *output formatting* rather than a fundamental inability of these models to understand or recommend poses. The claim should be refined to reflect that existing models fail to provide *structured and reliable* pose guidance under the current evaluation protocol, rather than implying a total lack of capability.
