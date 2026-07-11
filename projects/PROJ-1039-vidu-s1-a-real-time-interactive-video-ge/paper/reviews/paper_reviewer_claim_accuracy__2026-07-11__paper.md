---
action_items:
- id: c0eaea4112dd
  severity: writing
  text: The paper presents a compelling system for real-time interactive video generation,
    but several factual claims regarding hardware capabilities and baseline comparisons
    require precise alignment with the reported evidence. First, the abstract and
    Section 3.2 repeatedly claim the model runs at "up to 42 FPS on regular consumer
    GPUs." However, the experimental setup in Section 3.1 and the results in Table
    1 explicitly specify that these measurements were conducted on "RTX 5090 GPUs."
    The RTX 5090 is
artifact_hash: 46afb73f62a16a65e326f7d8ac4dd27cb539ff8a93c468cf40ba07e4be2d3109
artifact_path: projects/PROJ-1039-vidu-s1-a-real-time-interactive-video-ge/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T02:56:58.352303Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a compelling system for real-time interactive video generation, but several factual claims regarding hardware capabilities and baseline comparisons require precise alignment with the reported evidence.

First, the abstract and Section 3.2 repeatedly claim the model runs at "up to 42 FPS on regular consumer GPUs." However, the experimental setup in Section 3.1 and the results in Table 1 explicitly specify that these measurements were conducted on "RTX 5090 GPUs." The RTX 5090 is a high-end, likely unreleased or professional-grade card (depending on the exact 2026 context), and certainly not representative of a "regular consumer GPU" (e.g., RTX 3060/4070). This overstatement misleads readers about the accessibility of the real-time performance. The claim should be qualified to "high-end GPUs" or the specific hardware should be named to ensure accuracy.

Second, there is a potential citation drift or hallucination regarding baselines. The text in Section 1 and the context of Table 1 imply comparisons against leading commercial systems. While the bibliography includes entries for HeyGen and Kling Avatar 2.0, the text or table captions (if they referenced specific model versions like "GPT-5.5" or "Gemini-3.1" as suggested by the future-dated nature of the paper's timeline) must be verified. If the authors claim to compare against models that do not exist in the public record or are not cited in the bibliography, this constitutes an unsupported comparative claim. The bibliography provided does not list GPT-5.5 or Gemini-3.1; if these were used, they must be added; if not, the comparison claim must be removed or corrected to reflect the actual baselines used.

Finally, the claim of a "100% preference rate against HeyGen and LemonSlice" in Section 3.1 is a strong absolute statement. While the paper mentions this refers to "subject controllability," the quantitative table shows HeyGen achieving a CSIM of 0.9191, nearly identical to Vidu S1's 0.9192. To maintain rigor, the authors should ensure the "100%" figure is clearly scoped to the specific "subject controllability" metric of the human evaluation and not conflated with overall quality, or provide the specific breakdown of the A/B test results to substantiate the absolute win rate.

These issues are primarily matters of precision and scope rather than fundamental scientific flaws, but they are critical for the credibility of the performance claims.
