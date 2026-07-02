---
action_items:
- id: 4aba9e8c2fa5
  severity: writing
  text: The paper makes several claims that extrapolate beyond the provided evidence
    or lack necessary context, specifically regarding performance metrics, novelty,
    and the scope of "long-video" capabilities. First, the efficiency claims in the
    Abstract and Introduction ("30-180x faster," "real-time generation at 23.8 FPS")
    are heavily dependent on the specific hardware used (H200 GPU) and the architectural
    difference between the proposed autoregressive method and the bidirectional baselines.
    Table 1 sh
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:10:34.493234Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extrapolate beyond the provided evidence or lack necessary context, specifically regarding performance metrics, novelty, and the scope of "long-video" capabilities.

First, the **efficiency claims** in the Abstract and Introduction ("30-180x faster," "real-time generation at 23.8 FPS") are heavily dependent on the specific hardware used (H200 GPU) and the architectural difference between the proposed autoregressive method and the bidirectional baselines. Table 1 shows baselines evaluated on A100s or unspecified hardware, while the proposed method is on an H200. The paper fails to normalize these comparisons or acknowledge that the "real-time" claim is contingent on high-end, specific hardware. Furthermore, comparing the FPS of an autoregressive model (which generates frame-by-frame) directly against bidirectional models (which generate the whole sequence) without discussing the latency implications for short clips is misleading. The "30-180x" figure is a raw throughput ratio that may not translate to lower end-to-end latency for typical user interactions.

Second, the claim of **"consistent long-video extrapolation"** (Abstract, Section 4, Conclusion) is overstated. While the method supports generating videos longer than the training sequence (81 frames), the quantitative evidence in Table 2 (Ablation on 165 frames) shows only marginal improvements in ID consistency (Cur. score: 0.4232 vs 0.4265) when using the proposed Gradient-Reweighted DMD. The qualitative figures (Fig. app) demonstrate videos of limited duration. The term "consistent" implies a high degree of stability over time which is not strongly supported by the data, especially given the known challenges of autoregressive drift. The authors should qualify this to "extended video generation" or explicitly discuss the limits of coherence over time.

Third, the **novelty claim** in the Related Works section ("no research has yet explored streaming applications in customized video generation") is an over-generalization. The paper cites *MotionStream* and *LiveAvatar* as works that exploit streaming for interactive control. While those works may focus on continuous signals (audio, motion), the blanket statement ignores the broader context of interactive generation. The claim should be refined to specify that no prior work addresses *discrete, garment-level* switching in a streaming manner.

Finally, the **generalization claim** regarding "single-to-multiple generalization" (Intro) relies on a training strategy where the reference and garment images are mismatched. While this is a clever heuristic, the paper does not provide sufficient evidence that this generalizes to *arbitrary* garment combinations unseen during training, especially given the limited dataset size (62K triplets) and the reliance on a specific data curation pipeline. The claim that the model "implicitly preserves coherence" is a strong assertion that requires more rigorous ablation on out-of-distribution garment pairs to be fully justified.
