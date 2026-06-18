---
action_items:
- id: 68cc8220564a
  severity: science
  text: "Temper the claim that 38.2% of model outputs pose serious clinical harm;\
    \ the figure is based on a limited 89\u2011task clinician review sample and should\
    \ be presented as an indicative finding rather than a definitive prevalence across\
    \ the whole benchmark."
- id: e0e3fcbfce7e
  severity: writing
  text: "Add a clear limitation stating that MedMisBench evaluates only multiple\u2011\
    choice, answer\u2011grounded items and may not directly reflect epistemic resilience\
    \ in open\u2011ended or multi\u2011turn clinical dialogues."
- id: a7eb45776a62
  severity: science
  text: "Discuss the risk of contamination where commercial LLMs might have seen portions\
    \ of the source datasets during training, which could affect clean\u2011accuracy\
    \ and resilience measurements."
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:46:50.110273Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript introduces **MedMisBench**, a benchmark designed to assess “epistemic resilience” of large language models (LLMs) when misleading medical context is injected. While the experimental results convincingly show that clean‑accuracy does **not** guarantee resilience—e.g., clean accuracy averages 71.1 % but drops to 38.0 % under focused (Type 1) injections—the paper **overreaches** in a few key areas:

1. **Clinical‑harm extrapolation** – The authors report that a 14‑member, 7‑country clinician panel found “serious potential harm in 38.2 % of reviewed cases.” This statistic is derived from a **small, non‑representative sample** (89 reviewed items, 64 dual‑rated). Presenting it as a general property of LLMs under misleading context overstates the evidence. The paper should explicitly qualify this figure as a **preliminary observation** and avoid implying that the same proportion holds across the entire benchmark or real‑world deployments.

2. **Scope of the benchmark** – MedMisBench is limited to **answer‑grounded multiple‑choice questions**. The authors claim it “exposes a structural blind spot in LLM evaluation in medical settings,” yet they do not acknowledge that many clinical interactions are **open‑ended, multi‑turn, or multimodal**. Without this clarification, the claim suggests broader applicability than the benchmark actually provides.

3. **Potential data contamination** – The evaluation uses commercial APIs (GPT‑5.4, Gemini‑3.1, Claude‑sonnet) whose training data are not disclosed. The paper does not discuss the possibility that these models may have already encountered portions of the source datasets (e.g., MedQA, MedMCQA). This omission could inflate clean‑accuracy and affect the measured resilience loss, especially for models that have been fine‑tuned on similar medical corpora.

4. **Mitigation claims** – The defensive‑prompt and search‑based mitigations are presented as “helpful but incomplete.” However, the paper does not quantify the **statistical significance** of the observed improvements, nor does it discuss variability across model families. A more cautious interpretation is warranted.

Overall, the central empirical findings (high ASR under focused injections, taxonomy‑driven vulnerability patterns) are well‑supported by the data. The overreach lies primarily in **generalizing limited clinician‑review results** and **overstating the benchmark’s breadth** without sufficient caveats. Addressing these points will align the manuscript’s claims with the evidence presented.
