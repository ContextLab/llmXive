---
artifact_hash: de55394b12e45f35d14619842228dd7f355c964a3689a145deba5b04573843f5
artifact_path: projects/PROJ-571-co-evolving-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:43:33.852954Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes strong performance claims that exceed the statistical evidence provided. In the Abstract (line 24), the authors state CoPD "significantly outperform[s]" baselines. However, Tables 1 and 2 (lines 330-410) report only point estimates without standard deviations or statistical significance testing. Given the marginal gains over domain-specific experts (e.g., +1.2% on Image Avg in Table 1), the term "significantly" is an overreach without variance metrics or p-values to confirm the results are not due to random seed variance.

Similarly, the claim in the Introduction (line 127) that CoPD "surpasses domain-specific experts" requires qualification. While the means are higher, the ablation study (Table 3, line 450) shows the merged model's advantage over single branches is minimal (e.g., 57.71 vs 57.24 Overall Avg). Presenting this as a definitive breakthrough without discussing the statistical reliability overruns the data's support.

Furthermore, the paper lacks a dedicated Limitations section. In `paper.tex` (line 100), the `\input{limitations}` command is commented out. This omission is critical when claiming a "novel training scaling paradigm" (Conclusion, line 535). The evaluation is restricted to a single model scale (Qwen3-VL-4B) and specific reasoning domains. Extrapolating this to a general "scaling paradigm" without discussing computational overhead (training K branches vs 1) or performance on non-reasoning tasks constitutes overreach regarding the method's generality. The pilot study (Section 2.3, Fig 2) establishes a correlation ($r=0.89$) between overlap and gain but does not rule out confounding factors like data distribution shifts between the static and co-evolving pipelines.

To address these overreach issues, the authors should: (1) Replace "significantly" with "consistently" or add statistical tests; (2) Un-comment and populate the Limitations section to discuss compute costs and generalizability; (3) Temper the "scaling paradigm" claim to reflect the current experimental scope.
