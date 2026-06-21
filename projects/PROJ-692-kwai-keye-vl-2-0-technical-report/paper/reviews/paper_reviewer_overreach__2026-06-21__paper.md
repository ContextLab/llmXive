---
action_items:
- id: 4af62b4a0013
  severity: writing
  text: "The abstract and Section\u202F1 claim \u201Cstate\u2011of\u2011the\u2011\
    art performance\u201D on long\u2011video benchmarks, yet Table\u202F1 shows that\
    \ on several key metrics (e.g., MLVU accuracy, Video\u2011MME\u2011v2 non\u2011\
    linear scores) competing models outperform Keye\u2011VL\u20112.0. Revise the claim\
    \ to reflect only the benchmarks where it truly leads, and add a discussion of\
    \ where it falls short."
- id: 0dc6d7933671
  severity: science
  text: "The paper asserts \u201Clossless 256\u202FK token contexts via DeepSeek Sparse\
    \ Attention\u201D (Abstract, lines\u202F1\u20113) but provides no quantitative\
    \ analysis of information loss (e.g., perplexity or retrieval fidelity) compared\
    \ to dense attention. Include an ablation that measures degradation, or qualify\
    \ the claim as \u201Ceffectively maintains performance up to 256\u202FK tokens.\u201D"
- id: 93705759a2d2
  severity: writing
  text: "Section\u202F3 describes a staged curriculum up to 2\u202FT tokens of pre\u2011\
    training data, yet the total compute budget, hardware requirements, and carbon\
    \ cost are omitted. Add a clear limitation paragraph quantifying the resources\
    \ needed for reproducibility."
- id: 5b88a7f0a4e3
  severity: science
  text: "The manuscript promotes \u201Cagentic collaboration across Code, Tool, and\
    \ Search tasks\u201D (Abstract) but only reports results on LiveCodeBench, OJBench,\
    \ and a few tool benchmarks. No evaluation of search or multi\u2011turn planning\
    \ is presented. Either provide such evaluations or temper the claim to match the\
    \ presented evidence."
- id: 663f808ac1fa
  severity: writing
  text: "Claims of \u201Ccompetitive on coding, tool\u2011use, OCR, and visual reasoning\
    \ benchmarks\u201D ignore cases where Keye\u2011VL\u20112.0 is outperformed (e.g.,\
    \ BFCL\u2011V4 where Qwen3.5 scores higher). Add a balanced comparison and discuss\
    \ why the model lags on those tasks."
- id: 4b2171c7e9ac
  severity: writing
  text: "The paper does not discuss potential biases introduced by the massive multimodal\
    \ pre\u2011training data (DataComp, LAION, CC12M, etc.). Include a limitations\
    \ section addressing data quality, representation bias, and possible downstream\
    \ harms."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:52:26.644822Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several claims that extend beyond the evidence presented, raising concerns of over‑reach. In the abstract and the introductory paragraph (Section 1), the authors state that Keye‑VL‑2.0 achieves “state‑of‑the‑art performance” on long‑video comprehension and temporal localization. However, Table 1 (Video understanding results) shows that on the MLVU benchmark the Qwen3.5‑35B model attains a higher accuracy (85.6 %) than Keye‑VL‑2.0 (82.8 %). Similarly, on the Video‑MME‑v2 non‑linear metric, the larger Qwen‑VL‑235B model outperforms Keye‑VL‑2.0 (26.3/28.1 vs. 18.5/24.2). The claim should be qualified to reflect only the benchmarks where the model truly leads (e.g., LongVideoBench, TimeLens) and acknowledge where it falls short.

The paper also declares “lossless 256 K token contexts via DeepSeek Sparse Attention” (Abstract, lines 1‑3). No empirical measurement of information loss is provided; the only evidence is an inference‑cost table (Figure 2). Without a perplexity or retrieval‑fidelity analysis comparing dense versus sparse attention at 256 K length, the “lossless” assertion is unsupported. An ablation that quantifies any degradation, or a more cautious phrasing, is needed.

Section 3 outlines a four‑stage pre‑training curriculum culminating in 2 T tokens of data, yet the manuscript omits any discussion of the compute budget, hardware configuration, or environmental impact. Reproducibility and fairness require a clear statement of the resources consumed (GPU‑hours, memory footprint, carbon estimate).

The authors promote a “Cross‑Modal Multi‑Teacher On‑Policy Distillation (MOPD) with Context‑RL and Video‑RL, enabling agentic collaboration across Code, Tool, and Search tasks.” Yet the evaluation only includes code (LiveCodeBench, OJBench) and tool benchmarks (τ²‑Bench, VitaBench). No search or multi‑turn planning experiments are reported, making the claim about “agentic collaboration” over‑reaching. Either add appropriate search‑oriented evaluations or temper the claim.

Similarly, the statement that the model remains “competitive on coding, tool‑use, OCR, and visual reasoning benchmarks” overlooks cases where it is outperformed, such as BFCL‑V4 (Table 2) where Qwen3.5 scores higher. A balanced discussion of strengths and weaknesses across all evaluated tasks would improve honesty.

Finally, the paper lacks a limitations discussion concerning data bias. The pre‑training data sources (DataComp, LAION, CC12M, PD12M, COCO) are known to contain demographic and cultural biases. Addressing how these may affect downstream behavior, especially in the agentic use‑cases, is essential for responsible reporting.
