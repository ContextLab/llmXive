---
action_items:
- id: 0e07d819a1a2
  severity: writing
  text: The paper makes several claims that extend beyond the immediate scope of the
    provided evidence, particularly regarding the uniqueness of the benchmark and
    the absolute necessity of the proposed method. First, the claim in the Abstract
    and Introduction that MulTaBench constitutes the "largest image-tabular benchmarking
    effort to date" is an overreach. While the paper introduces 20 image-tabular datasets,
    Section 3.2 ("Image-Tabular Curation") acknowledges that existing benchmarks like
    MuG and BAG
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:49:05.743004Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate scope of the provided evidence, particularly regarding the uniqueness of the benchmark and the absolute necessity of the proposed method.

First, the claim in the Abstract and Introduction that MulTaBench constitutes the "largest image-tabular benchmarking effort to date" is an overreach. While the paper introduces 20 image-tabular datasets, Section 3.2 ("Image-Tabular Curation") acknowledges that existing benchmarks like MuG and BAG contain multiple datasets, some of which overlap. Without a rigorous deduplication and comparison of the *unique* dataset counts across all prior works (specifically BAG, which is cited as having 11 image-tabular datasets but may have more in its full scope), the superlative "largest" is not fully substantiated. The authors should either provide a direct comparison table of unique dataset counts or soften the claim to "one of the largest" or "the largest specifically curated for Target-Aware Representations."

Second, the paper frequently characterizes Target-Aware Representations (TAR) as "necessary" (Abstract) and states that frozen embeddings "fail" (Sec 1) to capture critical information. This language overstates the empirical findings. While the results consistently show that TAR outperforms frozen embeddings, the magnitude of improvement is often small (e.g., +0.003 to +0.012 in the per-dataset results in Appendix Table 1). In many cases, the performance gap is marginal, suggesting that frozen embeddings are not "failing" but rather that TAR offers a consistent, albeit sometimes small, boost. The paper should revise its language to reflect that TAR provides "consistent improvements" rather than being a strict requirement for success, and acknowledge that for some tasks, the gain is negligible.

Finally, the claim in Section 2 that "no existing model has successfully maintained SOTA performance on tabular tasks while learning TAR" is an overgeneralization. The paper evaluates a specific set of baselines (TabSTAR, ConTextTab, AutoGluon-Multimodal) and finds them lacking in specific contexts. However, it does not exhaustively test all possible joint-training architectures or recent multimodal foundation models that might have been released or are in development. The claim should be qualified to refer to the "evaluated baselines" or the "current landscape of explicitly tested models" rather than making a universal statement about the entire field.
