---
action_items:
- id: cc840e109b30
  severity: writing
  text: 'Abstract: The ''55%'' shortcut claim relies on a strict consensus threshold
    (c=3) in Table 5, while Table 3 shows 92.7% under relaxed conditions (c>=1). Scope
    the claim to ''under strict consensus'' or acknowledge the higher prevalence to
    avoid understating the issue.'
- id: 1ee96e3b6741
  severity: writing
  text: 'Abstract & Sec 4.2: Claiming SOTA models perform ''marginally above random''
    is inaccurate for Gemini-2.5-Pro (46.7% vs 25.6% baseline). Scope this to ''open-source
    Video-LLMs'' to avoid misrepresenting frontier proprietary model capabilities.'
- id: 6253ba12febc
  severity: writing
  text: 'Sec 5.2: The claim that reasoning strategy is ''as impactful as raw scale''
    lacks a scaling study. The oracle ensemble only compares modes within one model.
    Narrow to ''can close the gap between current open-source and frontier models''.'
artifact_hash: f0c16b304e278e372ae68ce72c73490fb948c6f63a71aa660ad21d1de4b7a1fb
artifact_path: projects/PROJ-1038-video-oasis-rethinking-evaluation-of-vid/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:06:00.323979Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a rigorous diagnostic framework, but the rhetoric in the abstract and conclusion occasionally exceeds the specific scope of the evidence provided in the tables.

First, the abstract highlights that "55% of existing benchmark samples are solvable without visual input." This figure is derived from the strict consensus threshold ($c=3$) in Table 5. However, Table 3 demonstrates that under a relaxed threshold ($c \ge 1$), the shortcut prevalence rises to 92.7%. By presenting the conservative lower bound as the primary finding without qualification, the abstract risks understating the severity of the problem for readers who do not immediately cross-reference the detailed tables. The claim should be contextualized to reflect that the "55%" figure represents a strict consensus estimate, or the abstract should acknowledge the significantly higher prevalence under relaxed conditions.

Second, the abstract and Section 4.2 assert that state-of-the-art models perform "only marginally above random guessing." This generalization is factually inaccurate when applied to the entire set of evaluated models. Table 7 clearly shows that the frontier model, Gemini-2.5-Pro, achieves 46.7% accuracy, which is nearly double the 25.6% random baseline. While the claim accurately describes the performance of open-source models (which hover around 26-36%), it incorrectly implies that *all* state-of-the-art models are failing at random levels. The text should explicitly scope this observation to "open-source Video-LLMs" to avoid misrepresenting the capabilities of the leading proprietary models.

Third, the conclusion in Section 5.2 claims that "strategic optimization of when to think can be as impactful as the raw scale of the model's architecture." This comparison is not supported by the experimental design. The "oracle ensemble" experiment compares a specific Qwen3-VL configuration against itself and a proprietary model, but it does not test "raw scale" across a range of model sizes (e.g., 7B vs 70B) to support a general claim about scaling laws. The claim should be narrowed to state that optimizing reasoning depth can bridge the performance gap between current open-source models and frontier proprietary models, rather than equating strategy with scaling.
