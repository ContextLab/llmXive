---
action_items:
- id: 72f31d5e495b
  severity: science
  text: The paper exhibits significant overreach in its claims regarding generalization
    and performance preservation, particularly where the data does not fully support
    the breadth of the conclusions. First, the claim of generalization to 256K and
    512K contexts (Abstract, Introduction, Section 6) is overstated. While the model
    outperforms the base Qwen2.5-VL-7B at these lengths, the performance at 512K (52.52)
    is lower than at 256K (55.09), indicating a degradation as context length increases
    beyond the
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:40:34.578358Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper exhibits significant overreach in its claims regarding generalization and performance preservation, particularly where the data does not fully support the breadth of the conclusions.

First, the claim of generalization to **256K and 512K contexts** (Abstract, Introduction, Section 6) is overstated. While the model outperforms the base Qwen2.5-VL-7B at these lengths, the performance at 512K (52.52) is lower than at 256K (55.09), indicating a degradation as context length increases beyond the training window. The paper frames this as "strong performance" and "generalization," but the data suggests the model is struggling to extrapolate effectively to 512K without further adaptation. The claim that it "exceeds baselines by over 20%" is also ambiguous; while the absolute gap is large, the relative improvement over a near-random baseline (19.49) is a statistical artifact rather than a demonstration of robust 512K capability. The paper must clarify the extent of this extrapolation and avoid implying that the model is fully capable at 512K when the trend shows declining performance.

Second, the claim of generalization to **webpage-based tasks** (Abstract, Section 6) is unsupported by the training data. The entire training corpus consists of PDF documents. Webpages have distinct structural properties (HTML, dynamic layouts, noise) compared to static PDFs. Claiming that a model trained exclusively on PDFs generalizes to "webpage-based multimodal needle retrieval" without task-specific supervision is an overreach. The paper should either provide evidence of robustness to webpage-specific noise or rephrase the claim to reflect that the model improves on *document-like* tasks, acknowledging the domain gap.

Third, the assertion that the recipe generalizes to **long-video understanding** (Abstract, Conclusion) conflates "long-context" with "temporal reasoning." The training data is static images of document pages. Video understanding requires modeling temporal dependencies and frame sampling strategies that are fundamentally different from static document retrieval. While the model shows improved scores on video benchmarks (Table 9), attributing this solely to the "LongPT recipe" for documents is an overclaim. The improvement may stem from general long-context attention mechanisms rather than specific video-relevant training. The paper should temper this claim to avoid implying that document training directly transfers to video temporal reasoning.

Finally, the claim that pure long-document VQA **"largely preserves short-context capabilities"** (Abstract, Section 5) is contradicted by the data in Table 4. The short-context average drops from 66.47 (base) to 65.48 (0% short data). While the drop is modest, it is a degradation, not preservation. The paper should revise this claim to "minimally degrades" or provide a more detailed breakdown of which short-context tasks are affected to avoid misleading readers about the trade-offs.

These overclaims undermine the paper's credibility. The authors must align their conclusions strictly with the empirical evidence, acknowledging the limitations of their training data (PDFs only) and the observed performance trends (degradation at 512K, short-context drop).
