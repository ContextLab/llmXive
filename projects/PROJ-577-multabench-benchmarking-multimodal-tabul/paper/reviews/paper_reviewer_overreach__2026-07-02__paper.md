---
action_items:
- id: 23a079b30679
  severity: writing
  text: The claim that MulTaBench is the 'largest image-tabular benchmarking effort
    to date' (Abstract, Sec 1) is an overreach. The paper acknowledges existing benchmarks
    like MuG and BAG but lacks a quantitative comparison of dataset counts or total
    samples to substantiate the 'largest' superlative. Please add a comparative table
    or explicit count comparison.
- id: fad63ad0d7c6
  severity: writing
  text: The assertion that 'no existing model has successfully maintained SOTA performance
    on tabular tasks while learning TAR' (Sec 1) is too absolute. The paper cites
    TabSTAR's limitations but lacks a direct, controlled experiment comparing a SOTA
    model with TAR against one without on a unified benchmark. This strong negative
    claim requires stronger evidence or softer phrasing (e.g., 'current models struggle
    to...').
- id: c57771904eea
  severity: writing
  text: The conclusion that 'TAR significantly outperforms frozen embeddings even
    at the larger scale' (Sec 5) overgeneralizes from specific encoders (DINO-v3,
    e5). The paper does not rule out that other architectures might inherently capture
    task-relevant signals without fine-tuning. Qualify the claim to reflect it holds
    for the specific family of encoders evaluated.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:47:36.042850Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the novelty and scope of MulTaBench and the necessity of Target-Aware Representations (TAR) that slightly exceed the immediate evidence provided.

First, the claim in the Abstract and Introduction that MulTaBench constitutes the "largest image-tabular benchmarking effort to date" is an overreach. While the paper introduces 20 image-tabular datasets, it does not explicitly quantify the total number of datasets or samples in prior benchmarks (e.g., MuG, BAG, or the image subsets of AutoGluon benchmarks) to substantiate the superlative "largest." Without a direct comparative count, this statement is an unsupported extrapolation.

Second, the Introduction asserts that "no existing model has successfully maintained SOTA performance on tabular tasks while learning TAR for text and images." This is a definitive negative claim. The paper supports this by citing TabSTAR's compromise on numerical performance and the limitations of PFNs, but it does not present a direct, controlled ablation where a SOTA tabular model is explicitly forced to learn TAR versus remaining frozen on a unified benchmark to prove the impossibility of the former. The evidence suggests a *trend* or *difficulty*, but the absolute phrasing overstates the conclusion.

Finally, the robustness analysis concludes that TAR outperforms frozen embeddings "even at the larger scale" (Sec 5). While the results for DINO-v3 and e5 are clear, the paper extrapolates this to imply a general property of embedding models. It does not consider that other pretraining objectives or architectures might inherently encode task-relevant signals without fine-tuning. The claim should be tempered to reflect that this finding holds for the specific class of encoders evaluated.

These issues are primarily matters of phrasing and scope definition rather than fundamental scientific flaws, but they require correction to ensure the claims are strictly supported by the data.
