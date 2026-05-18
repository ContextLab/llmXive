---
action_items:
- id: 6d7001908d74
  severity: writing
  text: Correct the claim that LoCoMo retains visual modalities; the cited work is
    text-only. Update Section 1 and Section 2 to accurately reflect LoCoMo's text-only
    nature.
- id: ae329aa3f800
  severity: writing
  text: Verify that specific model versions (e.g., GPT-5.4, Gemini-3.1-Pro) are explicitly
    supported by the cited system cards to ensure accurate attribution.
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-05-18T14:23:18.369326Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark, but several factual claims regarding related work and model specifications are not accurately supported by the provided citations.

First, in Section 1 (Introduction) and Section 2 (Related Work), the authors state that "Multimodal conversational benchmarks such as LoCoMo~\cite{maharana2024evaluatinglongtermconversationalmemory}... retain both visual and text modalities". The cited paper (Maharana et al., 2024) describes LoCoMo as a text-only benchmark for long-term conversational memory. Claiming it retains visual modalities is factually incorrect. This error is significant because the paper's core motivation relies on the gap between existing benchmarks: it argues that text-only benchmarks (like LongMemEval) overlook visuals, while multimodal ones (like LoCoMo) allow text-only shortcuts. If LoCoMo is text-only, the authors must rephrase this to accurately reflect the landscape (e.g., acknowledging LoCoMo as text-only and clarifying that Mem-Gallery is the multimodal counterpart). This misrepresentation weakens the claim that MemLens fills a unique multimodal gap.

Second, regarding model versions, Section 4.1 cites "GPT-5.4~\citep{singh2025openaigpt5card}". The citation refers to an "OpenAI GPT-5 System Card". While plausible in a future-dated context, the specific version "5.4" should be explicitly validated against the system card's versioning to ensure the citation supports the specific capabilities (e.g., context window size, multimodal grounding) attributed to it. Similarly, "Gemini-3.1-Pro"~\citep{googledeepmind2026gemini31pro} and "Claude Sonnet 4.5"~\citep{anthropic2025claudesonnet45card} are cited; ensure these specific version numbers match the released system cards referenced.

These issues require textual corrections to ensure factual alignment with the cited literature. They do not invalidate the experimental results but affect the accuracy of the related work summary and model attribution.
