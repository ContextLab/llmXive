---
action_items:
- id: 06eca977cad4
  severity: science
  text: "The manuscript repeatedly refers to per\u2011repo LoRA as an \u201Cupper\
    \ bound\u201D. Since per\u2011repo LoRA is itself a learned baseline and not provably\
    \ optimal, this phrasing overstates its status. Re\u2011word to describe it as\
    \ a strong baseline rather than an upper bound."
- id: eb1e0f67be1d
  severity: science
  text: "The OOD evaluation (Table\u202F5) shows higher exact\u2011match scores, but\
    \ the authors note that OOD targets are shorter, which can inflate EM. Provide\
    \ a controlled analysis (e.g., normalize target length or report length\u2011\
    adjusted metrics) to substantiate the claim of \u201Cstrong generalization\u201D\
    ."
- id: cd5e1d0f7be6
  severity: writing
  text: "The claim that Code2LoRA \u201Cconsistently gains over context\u2011injection\
    \ and fine\u2011tuning baselines\u201D should be qualified to reflect the modest\
    \ OOD margin (\u22481.8\u202Fpp) and the fact that some baselines (e.g., FFT\u2011\
    RAG) close the gap on certain splits. Adjust the language to avoid overstating\
    \ superiority."
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:46:08.997036Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper introduces Code2LoRA, a hypernetwork that generates repository‑specific LoRA adapters for code LLMs. While the experimental results are impressive, several statements extend beyond what the presented data justify.

1. **Upper‑bound terminology** – In the abstract and results (e.g., “matching the per‑repo LoRA upper bound”), the authors treat per‑repo LoRA as an optimal ceiling. However, per‑repo LoRA is itself a learned method and can be outperformed (as shown by Code2LoRA’s higher IR EM). This mischaracterizes the baseline and overstates the claim of matching an “upper bound”.

2. **OOD generalization claim** – Table 5 reports OOD EM improvements of ~1.8 pp over the next‑best baseline. The authors acknowledge that OOD targets are shorter, which systematically raises EM for all methods. Without a length‑controlled analysis, the assertion of “strong generalization” is not fully supported.

3. **“Consistent gains” phrasing** – Across static, evolution, and OOD tracks the paper states that Code2LoRA “consistently outperforms all baselines”. While it does lead on most metrics, the margin varies (e.g., only a 0.2 pp gain on the evolution IR split over per‑repo LoRA). The language should be tempered to reflect these nuances.

4. **Inference‑time token cost** – The claim of “zero inference‑time token overhead” is accurate regarding input length, but the paper does not discuss the latency of generating adapters on‑the‑fly (even if sub‑10 ms). This could be clarified to avoid implying that there is no runtime cost at all.

Overall, the methodology and empirical setup are sound, but the manuscript overreaches in its framing of baselines and generalization. Addressing the points above will align the claims with the evidence and improve scientific rigor.
