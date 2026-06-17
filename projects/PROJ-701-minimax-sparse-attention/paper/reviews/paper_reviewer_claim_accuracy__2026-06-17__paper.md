---
action_items:
- id: 9a227682adad
  severity: fatal
  text: "Several in\u2011text citations refer to works that are not present in the\
    \ bibliography (e.g., \\citep{kimiteam2025kimilinearexpressiveefficient}, \\citep{yang2025gateddeltanetworksimproving},\
    \ \\citep{deepseekai2025deepseekv32pushingfrontieropen}). Add the missing bibliography\
    \ entries or remove/replace the citations."
- id: e2ac456e9889
  severity: writing
  text: "The abstract and efficiency section claim a 28.4\xD7 FLOPs reduction and\
    \ 14.2\xD7/7.6\xD7 wall\u2011clock speedups. These numbers are supported by Figure\u202F\
    8 and Table\u202F1, but the caption of Figure\u202F8 does not explicitly state\
    \ the exact speedup values. Clarify the measured speedup numbers in the figure\
    \ caption or text to ensure the claim is directly traceable to the presented data."
- id: 18f55db4f646
  severity: writing
  text: "The statement that \u201Cthe quadratic\u2011cost softmax attention is the\
    \ primary culprit\u201D is made without a supporting citation. Provide a reference\
    \ (e.g., Vaswani et\u202Fal., 2017) to substantiate this claim."
- id: 3f486ec87622
  severity: writing
  text: "In the introduction, several future\u2011dated references (e.g., \\citep{openai2025gpt5},\
    \ \\citep{anthropic2025claude46}) are used to support a claim about current trends.\
    \ Verify that these sources are publicly available and appropriate; if they are\
    \ press releases rather than peer\u2011reviewed work, consider rephrasing the\
    \ claim or citing more established literature."
- id: f9f00b7670ab
  severity: writing
  text: "Ensure that all performance comparisons (e.g., \u201Con par with GQA\u201D\
    ) are explicitly linked to the corresponding tables/figures (Table\u202F1, Table\u202F\
    2). Adding a brief sentence referencing the exact rows that demonstrate parity\
    \ will improve claim traceability."
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:26:43.195836Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several quantitative claims that are generally backed by the presented experiments, but there are notable citation gaps that affect claim verifiability.  

1. **Missing bibliography entries** – The text cites several 2025/2026 works (e.g., `kimiteam2025kimilinearexpressiveefficient`, `yang2025gateddeltanetworksimproving`, `deepseekai2025deepseekv32pushingfrontieropen`) that do not appear in `references.bib`. Without these entries, the reader cannot verify the statements they support, which violates the claim‑accuracy requirement.  

2. **Performance claims** – The abstract’s claim of a 28.4× FLOPs reduction at 1 M tokens is corroborated by the FLOPs analysis in §6 and Figure 8 (left sub‑figure). The reported 14.2× prefill and 7.6× decoding speedups are shown in the middle and right sub‑figures of Figure 8, but the figure caption does not list the exact numbers, making the link less explicit. Adding a concise statement in the caption (e.g., “Measured speedups: 14.2× prefill, 7.6× decode at 1 M context”) would close this gap.  

3. **Uncited foundational claim** – The statement that quadratic‑cost softmax attention is the primary bottleneck lacks a citation. A standard reference such as Vaswani et al., 2017 should be added.  

4. **Future‑dated citations for trend description** – The introduction cites several 2025/2026 model announcements to justify the claim that LLMs are shifting toward ultra‑long contexts. These sources may be press releases or non‑peer‑reviewed materials; their availability and suitability should be verified, or the claim should be re‑worded to rely on established literature (e.g., OpenAI GPT‑4 technical report, DeepMind’s scaling papers).  

5. **Explicit linking of “on‑par with GQA”** – While Table 1 shows comparable or better scores for most benchmarks, the manuscript does not explicitly point the reader to the rows that demonstrate parity. Adding a brief sentence like “Across the full suite (Table 1, rows X–Y), MSA matches or exceeds GQA performance” would make the claim directly traceable.  

Overall, the empirical evidence for the core efficiency and quality claims is present, but the citation inaccuracies and occasional lack of explicit linkage reduce the claim‑accuracy reliability. Addressing the missing references and tightening the textual links to the figures/tables will bring the manuscript into compliance.
