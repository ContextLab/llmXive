---
action_items:
- id: b90e05feb08a
  severity: science
  text: "Report variance (e.g., standard deviation or confidence intervals) for all\
    \ quantitative tables (e.g., Table\u202F1, Table\u202F2, Table\u202F3) and perform\
    \ appropriate statistical significance tests to support claims of improvement."
- id: bd188e8f0e12
  severity: science
  text: "Clarify the exact number of unique decks evaluated per persona\u2011intent\
    \ pair and per model family; the current description (49 runs) conflates runs\
    \ with distinct evaluation units."
- id: 6d5f1fcf493f
  severity: science
  text: "Provide a power analysis or justification that the matched\u2011pair tool\u2011\
    memory evaluation (9 pairs) is sufficient to draw reliable conclusions, or increase\
    \ the number of pairs."
- id: 5c766fc00288
  severity: science
  text: "Include effect size measures (e.g., Cohen's d) for the persona\u2011alignment\
    \ gains to contextualize practical significance beyond raw score differences."
- id: 75cd48e930dc
  severity: science
  text: Document the randomization procedure for selecting source materials, personas,
    and modify requests to rule out selection bias.
- id: 91ed05f47ea4
  severity: science
  text: "Address potential p\u2011hacking by pre\u2011registering evaluation protocols\
    \ or explicitly stating that all reported metrics were defined a priori."
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:19:32.935731Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a hierarchical memory framework (MemSlides) and evaluates three core claims: (1) user‑profile memory improves round‑0 persona alignment, (2) tool‑memory enhances localized multi‑turn revision reliability, and (3) working memory enables intra‑session preference carry‑over. The evidence consists of controlled experiments with three LLM families (GPT‑5, GLM‑5, Gemini 3.1 Pro) and a multi‑persona, multi‑intent profile bank (30 entries). 

**Sample size and replication.** The profile‑memory experiments involve 49 generation runs (≈ 1.6 runs per persona‑intent per model) and three blind judges per dimension, yielding aggregated scores in Table 1. However, the paper does not report how many distinct decks contributed to each mean, nor does it provide variance or confidence intervals. Without these, it is impossible to assess the stability of the reported improvements (e.g., GLM‑5 gains of +2.78 on Content). The tool‑memory evaluation is a diagnostic matched‑pair study with only nine pairs (three per model). While the authors perform a sign test, the sample is too small to robustly support the claim that tool‑memory “generally improves” edit reliability; the p‑values for Closed‑Loop Completion (p = 0.3125) are non‑significant.

**Effect size and statistical rigor.** The manuscript reports raw mean differences (e.g., +2.42 overall persona‑alignment for GPT‑5) but omits effect‑size metrics. Given the 0–10 rating scale, a 2‑point increase could be substantial, but this cannot be judged without dispersion measures. Moreover, no correction for multiple comparisons is discussed despite evaluating four dimensions across three models.

**Risk of p‑hacking / protocol transparency.** The evaluation protocol is described in the appendix, yet the selection of the nine modify pairs is said to be “selected before inspecting pair outcomes,” but the criteria for selection are not quantified. This leaves open the possibility of cherry‑picking favorable cases. Pre‑registration or a clear statement that all measured metrics were pre‑specified would mitigate this concern.

**Robustness to alternative explanations.** The authors argue that persona‑alignment gains are not driven by template matching because the Structure metric excludes template fit. This is a reasonable control, but the paper does not test whether the same gains persist when using a different judging pool or when varying the number of blind votes per deck. Similarly, the tool‑memory benefits could be confounded by differences in tool‑call latency unrelated to memory; the Core Tool Time Ratio attempts to control for this, yet the underlying distribution of tool‑call durations is not shown.

**Recommendations.** To strengthen the scientific evidence, the authors should (i) report per‑condition variance and conduct hypothesis tests (e.g., paired t‑tests) for all claimed improvements; (ii) provide effect‑size statistics; (iii) increase the size of the matched‑pair tool‑memory study or supplement it with a larger random sample; (iv) detail randomization and selection procedures to rule out bias; and (v) consider a replication study with an independent set of judges. Addressing these points will make the central claims more robust and defensible.
