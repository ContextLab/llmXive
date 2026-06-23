---
action_items:
- id: 823876a96e0a
  severity: science
  text: "The claim that working memory supports session\u2011level preference carryover\
    \ is only backed by qualitative figures (Appendix\u202FFig.\u202F9). Provide a\
    \ systematic quantitative evaluation (e.g., controlled ablation or statistical\
    \ analysis) to substantiate this claim."
- id: 6e4c3019e121
  severity: writing
  text: "Clarify whether the profile\u2011memory and tool\u2011memory ablations control\
    \ for all other variables (e.g., template usage, prompt phrasing). Explicitly\
    \ state that the only difference between conditions is the memory injection to\
    \ avoid implicit causal assumptions."
- id: 3e5e41718912
  severity: writing
  text: "In Section\u202F3, the problem formulation is presented twice with slightly\
    \ different notation (e.g., $z_t$ vs $U(z_{t-1},f_t)$). Consolidate the formulation\
    \ to avoid potential confusion about the role of session state."
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:18:53.125604Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The manuscript presents a hierarchical memory framework (long‑term user profile memory, tool memory, and working memory) for personalized slide generation and multi‑turn localized revision. The logical flow of the paper is generally coherent: the authors define the memory components, describe how they are integrated into the generation and edit pipelines, and then report experimental results that aim to isolate the effect of each memory type.

**Supported causal claims**

1. **Profile‑memory improves persona‑alignment** – The authors compare MemSlides with and without profile‑memory while keeping model family, source material, intent, and template constant (Appendix A.1). The reported persona‑alignment scores (Table 5) show consistent improvements over both DeepPresenter and SlideTailor for GLM‑5 and Gemini 3.1 Pro, and selective gains for GPT‑5. The experimental design matches the claim, and the discussion correctly acknowledges the one dimension (Structure) where DeepPresenter remains higher.

2. **Tool‑memory improves localized edit reliability** – The diagnostic matched‑pair study (Table 6, Table 7, Table 8) isolates tool‑memory injection as the only variable. Aggregate metrics (higher Closed‑Loop Completion and Strict Verify, lower edit latency and core‑tool‑time ratio) support the claim, and the authors transparently report pair‑level heterogeneity and a paired sign‑test. The conclusion that tool‑memory “is associated with” better edit behavior is logically consistent with the evidence.

**Logical gaps / insufficient support**

1. **Working‑memory effect** – The paper asserts that working memory “supports session‑level preference carryover” (Section 3, contributions, and Figure 9). The only evidence provided is a pair of qualitative examples (Appendix Fig. 9) showing visual style carryover across turns. No quantitative ablation or statistical analysis is presented to demonstrate that the working‑memory component causally improves any measurable metric (e.g., higher persona‑alignment after multiple turns, reduced drift, or faster convergence). As a result, the claim extends beyond the presented data, creating a logical leap from anecdotal illustration to a general conclusion.

2. **Potential confounding variables** – While the profile‑memory and tool‑memory ablations are described as “identical except for memory injection,” the manuscript does not explicitly confirm that other factors (e.g., template selection, prompt phrasing, or hidden system identifiers) are held constant. Without a clear statement, readers may infer an unsupported causal link between memory injection and performance improvements.

3. **Redundant problem formulation** – Section 3 contains two overlapping formulations of the multi‑turn generation problem (Equations 1–2 and the later block). The notation for the session state ($z_t$, $U$, $A_t$) differs slightly, which could lead to ambiguity about the exact role of working memory. This redundancy does not break logical consistency but hampers clarity and may cause misinterpretation of the underlying assumptions.

**Overall assessment**

The core logical structure—introducing hierarchical memory, isolating its components, and demonstrating their impact through controlled experiments—is sound. The primary claims about profile‑memory and tool‑memory are adequately supported by the presented quantitative results. The main logical deficiency lies in the insufficient empirical backing for the working‑memory claim and the need for explicit confirmation that all other variables are truly controlled in the ablation studies.

Addressing these points will strengthen the logical rigor of the manuscript.
