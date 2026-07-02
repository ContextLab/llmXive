---
action_items:
- id: abf7c61a4a9e
  severity: science
  text: The paper contains multiple critical factual inaccuracies and citation errors
    that undermine the validity of its core claims. First, the training budget is
    cited as "5B (2605.13831, https://arxiv.org/abs/2605.13831)-token budget" in the
    Abstract and Introduction. The arXiv ID 2605.13831 corresponds to a future date
    (May 2026) and the URL is unreachable. The number 2605.13831 appears to be a hallucinated
    value or a corruption of a different identifier. This renders the specific claim
    about the tr
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:39:55.854409Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: full_revision
---

The paper contains multiple critical factual inaccuracies and citation errors that undermine the validity of its core claims.

First, the training budget is cited as "5B (2605.13831, https://arxiv.org/abs/2605.13831)-token budget" in the Abstract and Introduction. The arXiv ID 2605.13831 corresponds to a future date (May 2026) and the URL is unreachable. The number 2605.13831 appears to be a hallucinated value or a corruption of a different identifier. This renders the specific claim about the training budget's source and magnitude unsupported.

Second, the paper repeatedly cites non-existent or future-dated models to support claims about the state of the art. Specifically, "Gemini 3.1" and "GPT-5.4" are cited as existing models with 128K+ context windows (Introduction, Related Work). These models do not exist in the current public domain, and the associated citations point to unreachable or future-dated arXiv IDs. This suggests the paper is either hallucinating the existence of these models or relying on a fictional timeline, which invalidates the context-setting claims.

Third, there are internal citation mismatches. In Section 5, the text states that the best performance for the extraction-to-reasoning ratio was found in `\cref{tab:vqa_effectiveness}`. However, `tab:vqa_effectiveness` compares VQA vs. OCR tasks, while the ratio ablation is actually presented in `tab:extract_reason_ratio`. This error misdirects the reader regarding the evidence for the 8:2 mixture claim.

Finally, several claims regarding data statistics (e.g., the 1.5 million document pool) lack immediate supporting citations in the main text, relying instead on appendix tables which may not be sufficient for a primary factual claim in the body. The unresolved claim markers (e.g., `c_72b83896`, `c_9ec9529c`) further indicate that the authors have not verified the sources for these specific numerical claims.

These issues are not merely stylistic; they strike at the heart of the paper's credibility. The reliance on non-existent models and invalid citations for key metrics (training budget, SOTA baselines) means the claims cannot be verified or reproduced. A full revision is required to correct these citations, remove references to non-existent models, and ensure all numerical claims are backed by valid, accessible sources.
