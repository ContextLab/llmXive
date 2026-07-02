---
action_items:
- id: c3c5d18d7fd1
  severity: science
  text: The claim that Keye-VL-2.0 'pioneers the application of Multimodal DeepSeek
    Sparse Attention (DSA) in the visual domain' (Introduction) is unsupported. The
    cited source (deepseek2025v32) describes DSA for text-only LLMs. The paper provides
    no evidence that the cited work or any prior art applied DSA to visual tokens,
    making the 'pioneer' claim potentially overstated without a specific citation
    for the visual adaptation.
- id: 1681fc1a646f
  severity: writing
  text: The abstract and Introduction claim 'lossless 256K context processing' and
    'losslessly' handling video contexts. However, Section 1.2 explicitly describes
    an 'Adaptive Video Pixel Budget' with scaling factors (0.125, 0.25, 0.5, 1.0)
    for videos exceeding 256s. This implies information reduction (subsampling) for
    long videos, contradicting the 'lossless' claim. The term should be qualified
    (e.g., 'lossless up to X duration' or 'context-efficient').
- id: b5fd56f5a21e
  severity: writing
  text: Table 1 (Video Understanding) lists 'Video-MME-v2 Non-Lin' scores where Keye-VL-2.0
    (18.5/24.2) is significantly lower than Qwen3-VL 235B (26.3/28.1), yet the text
    below the table states Keye-VL-2.0 'achieves best results on... Video-MME-v2 accuracy'.
    While the 'ACC' row supports this, the inclusion of the 'Non-Lin' row in the same
    table without clarification creates ambiguity about the 'best results' claim across
    the full benchmark suite.
- id: 93974cf5d71a
  severity: writing
  text: The citation 'openai2026gpt55' (Introduction) refers to a 2026 report for
    'GPT-5.5'. Given the current date context of the paper (2026), this is a future-dated
    citation. While acceptable for a preprint in that timeline, the claim that this
    model 'demonstrates substantial progress' relies on a source that may not be publicly
    verifiable or stable at the time of review, requiring the authors to ensure the
    URL and data are accessible.
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:25:13.217942Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several strong factual claims regarding the novelty and performance of the Kwai Keye-VL-2.0 model. While the technical depth is high, a few claims regarding "pioneering" status and "lossless" processing require tighter alignment with the provided evidence and citations.

First, the Introduction (Section 1) asserts that the authors "pioneer the application of Multimodal DeepSeek Sparse Attention (DSA) in the visual domain," citing `deepseek2025v32`. A review of the provided bibliography shows that `deepseek2025v32` is a technical report for a text-only LLM (DeepSeek-V3.2). The paper does not cite any prior work that applied DSA to visual tokens, nor does it explicitly state that the cited paper *only* covered text. If the application of DSA to vision is indeed a novel contribution of this work, the claim is valid but should be phrased to distinguish between the *method* (from DeepSeek) and the *application domain* (novel here). If DSA for vision was previously explored, the "pioneer" claim is factually incorrect. The current phrasing risks overstating the novelty of the *method* itself rather than its *application*.

Second, the Abstract and Introduction repeatedly claim "lossless 256K context processing" and "losslessly" handling video contexts. However, Section 1.2 ("Unified Visual Encoding") explicitly details an "Adaptive Video Pixel Budget" where videos longer than 256s are processed with scaling factors of 0.125, 0.25, or 0.5. This mechanism inherently reduces the number of visual tokens (and thus information) for long videos to fit the context window. Describing this as "lossless" is factually inaccurate; it is "context-efficient" or "lossy compression with adaptive scaling." The term "lossless" should be removed or strictly qualified to apply only to the context window management, not the visual content itself.

Third, in Section 4.1 (Video Understanding), the text below Table 1 states: "Keye-VL-2.0 achieves best results on LongVideoBench and Video-MME-v2 accuracy." While the "ACC" row in Table 1 supports this, the table also includes a "Non-Lin" (Non-Linear) row for Video-MME-v2, where Keye-VL-2.0 scores 18.5/24.2, significantly lower than the Qwen3-VL 235B baseline (26.3/28.1). The claim of "best results" is ambiguous without specifying that it applies only to the "ACC" metric, potentially misleading readers about the model's performance on the full benchmark suite.

Finally, the paper relies on several future-dated citations (e.g., `openai2026gpt55`, `anthropic2026claude`, `deepmind2026gemini`). While consistent with the paper's 2026 timeline, the validity of claims comparing against these models depends entirely on the existence and stability of these future reports. The authors should ensure these references are accessible or clearly marked as "forthcoming" if they are not yet public.
