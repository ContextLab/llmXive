---
action_items:
- id: 041ab0615787
  severity: science
  text: "The paper reports point estimates of accuracy improvements (e.g., Table\u202F\
    \ref{tab:main_results} shows +2.4\u202Fpts step accuracy for Terminal\u2011Bench\u2011\
    Evo) without any measure of variability (standard deviations, confidence intervals,\
    \ or statistical significance tests). This makes it impossible to assess whether\
    \ the gains are robust or could be due to random seed effects."
- id: ccb1e5498018
  severity: science
  text: "Experiments appear to be run with a single random seed per model/agent configuration.\
    \ Provide results over multiple seeds (e.g., \u22655) and report variance to rule\
    \ out seed\u2011specific performance fluctuations."
- id: 9b271fe1753e
  severity: science
  text: "The benchmark subsets have relatively modest sample sizes (e.g., 352 versioned\
    \ tasks for Terminal\u2011Bench\u2011Evo, 493 chain\u2011step slots for SWE\u2011\
    Chain\u2011Evo, 505 OOD questions for PersonaMem\u2011Evo). Discuss the statistical\
    \ power of these sample sizes and consider augmenting the datasets or performing\
    \ power analyses."
- id: a45d3df18f6a
  severity: science
  text: "There is no ablation or control condition isolating the effect of EvoMem\u2019\
    s components (e.g., patch retrieval vs. base memory, size of patch history). Include\
    \ ablation studies to demonstrate which aspects of EvoMem drive the reported gains."
- id: 4753f392dd83
  severity: science
  text: "The evaluation mixes many heterogeneous models (GPT\u20115.5, Gemini\u2011\
    3.1\u2011Pro, Kimi\u2011K2.6, etc.) but does not control for model size, training\
    \ data, or inference settings. Ensure fair comparisons by normalizing for these\
    \ factors or explicitly reporting them."
- id: ae8c3cece044
  severity: science
  text: "Efficiency\u2013accuracy trade\u2011off analysis (Figure\u202F\ref{fig:token_accuracy_efficiency})\
    \ lacks statistical testing; the visual trends could be driven by outliers. Provide\
    \ quantitative analysis (e.g., correlation coefficients with significance) to\
    \ support the claims."
- id: 40607a82efa8
  severity: science
  text: "The paper claims that EvoMem improves evidence capture (e.g., Table\u202F\
    \ref{tab:persona_capture_by_ood}) but does not define a clear statistical metric\
    \ for \u2018evidence capture\u2019 nor report uncertainty. Clarify the metric\
    \ and provide statistical validation."
- id: 0fabc4e418a5
  severity: science
  text: "Potential p\u2011hacking risk: multiple tables report many small improvements\
    \ (e.g., +0.4\u202Fpts, +1.2\u202Fpts) without correction for multiple comparisons.\
    \ Apply appropriate statistical corrections (e.g., Bonferroni) or pre\u2011register\
    \ hypotheses."
artifact_hash: 6cdb16771eea5c1aa0e0ff5e854ffcdbbe5d0a407e5c9d421612d453db08e7c6
artifact_path: projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T18:54:03.602050Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript introduces EvoArena, a benchmark suite for evaluating LLM agents under persistent environment evolution, and EvoMem, a patch‑based memory augmentation. While the benchmark construction is detailed (e.g., Sections \ref{sec:terminal_bench_evo}, \ref{sec:swe_chain_evo}, and \ref{sec:persona_mem_evo}), the empirical evidence supporting the central claim—that EvoMem consistently improves agent performance—lacks statistical rigor.

Key issues:

1. **Absence of Variability Measures** – All performance numbers (e.g., step and chain accuracies in Table \ref{tab:main_results} and Table \ref{tab:typical_results}) are presented as single percentages. No standard deviations, confidence intervals, or significance tests are provided, making it impossible to judge the reliability of the reported gains.

2. **Single‑Seed Evaluation** – The experimental setup (Section \ref{appendix:exp_setting}) does not mention multiple random seeds or repeated runs. Given the known sensitivity of LLM agents to initialization and sampling randomness, this raises concerns about reproducibility.

3. **Limited Sample Sizes** – The benchmark subsets contain a few hundred instances (e.g., 352 evolved terminal tasks, 493 SWE chain steps, 505 persona questions). The paper does not discuss whether these sample sizes afford sufficient statistical power to detect the modest improvements reported (often ≤ 2 pts).

4. **Lack of Ablation Controls** – EvoMem comprises several components (patch generation, retrieval, concatenation). The current results conflate all of them; there is no ablation study isolating the contribution of each component, nor a baseline that uses a naïve memory without patches.

5. **Heterogeneous Model Comparisons** – Results aggregate across models of differing scale and architecture (GPT‑5.5, Gemini‑3.1‑Pro, Kimi‑K2.6, etc.) without controlling for model size or training data. This confounds the interpretation of EvoMem’s effect versus inherent model capabilities.

6. **Efficiency Analysis Without Statistical Support** – Figure \ref{fig:token_accuracy_efficiency} visualizes token usage versus accuracy, but the manuscript does not quantify the relationship (e.g., correlation coefficients) nor test whether observed differences are statistically significant.

7. **Evidence Capture Metric Ambiguity** – Tables \ref{tab:persona_capture_by_ood} and \ref{tab:personamem_breakdown} report percentage improvements in “evidence capture” and question‑type accuracy, yet the definition of the metric and its statistical validation are unclear.

8. **Multiple Comparison Concerns** – Numerous small effect sizes are reported across many tables. Without correction for multiple hypothesis testing, there is a risk of false positives (p‑hacking).

To strengthen the scientific evidence, the authors should:

- Run each experiment with multiple random seeds (≥ 5) and report mean ± standard deviation.
- Perform statistical significance testing (e.g., paired t‑tests or non‑parametric equivalents) and report p‑values with appropriate corrections.
- Include ablation experiments that isolate EvoMem’s components.
- Provide a power analysis or justify the chosen dataset sizes.
- Standardize model comparisons by controlling for model size or reporting detailed model specifications.
- Quantify the token‑efficiency relationship with statistical metrics.
- Clearly define and statistically validate the “evidence capture” measure.

Addressing these points will make the central claims about EvoMem’s efficacy robust and reproducible.
