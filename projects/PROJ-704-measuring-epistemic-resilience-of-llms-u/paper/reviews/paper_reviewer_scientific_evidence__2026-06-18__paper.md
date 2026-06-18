---
action_items: []
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:47:29.717384Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.5
verdict: accept
---

The manuscript presents a well‑designed benchmark, **MedMisBench**, to quantify *epistemic resilience* of LLMs when faced with misleading medical context. The experimental evidence is robust across several dimensions:

1. **Sample Size and Diversity** – The benchmark comprises **10,932** answer‑grounded medical items drawn from five distinct source datasets (Table A.1). This yields **48,889** option‑level misleading‑context pairs, providing ample statistical power to detect differences across model families, reasoning settings, and taxonomy axes. The authors also report per‑dataset retention rates (≈ 42 % of source items), ensuring that the sample is not overly filtered.

2. **Control Conditions** – Clean accuracy is measured on the original items (Section 4.1) before any injection, establishing a baseline for each model. The two delivery protocols (Type 1 focused injection vs. Type 2 all‑option bundle) serve as controlled manipulations of the evidence environment (Section 3.4). This design isolates the effect of a single plausible false claim from the effect of competing evidence, allowing a clean causal interpretation of the observed performance drops.

3. **Replication Across Model Configurations** – The study evaluates **11** model configurations, spanning commercial APIs (GPT‑5.4, Gemini‑3.1‑pro, Claude‑sonnet‑4.6), open‑weight general‑domain models (Gemma‑4 26B, Qwen3.6‑27B), and a medical‑domain model (MedGemma 27B). Results are consistently reported for each model in the main text (Figures 4–6) and fully tabulated in the appendix (Tables C.1–C.3). The convergence of findings across such heterogeneous systems strengthens external validity.

4. **Effect Size Reporting** – The authors provide absolute and relative metrics: clean accuracy (71.1 %), Type 1 accuracy (38.0 %), and attack success rate (ASR = 51.5 %). They also report targeted ASR (TASR = 45.4 %) and stratify by content‑corruption and provenance (Figures 5–6, Tables A.5–A.6). These effect sizes are large enough to be practically meaningful (e.g., a 33‑point accuracy drop under focused injection).

5. **Statistical Rigor and Avoidance of P‑hacking** – No data‑driven selection of “best‑performing” models is performed; all models are evaluated on the same fixed benchmark. The authors pre‑register the taxonomy and injection pipeline (Appendix A.3) and release the static benchmark, preventing post‑hoc tuning. Confidence intervals are reported for clinician‑review outcomes (Section 4.4), demonstrating appropriate uncertainty quantification.

6. **Robustness Checks** – Two sensitivity analyses are included: (a) generator‑sensitivity using GPT‑5.4 to re‑create injections (Appendix D.1) shows negligible changes in ASR; (b) provenance‑assignment sensitivity (Appendix D.2) confirms that the main taxonomy effects persist under cyclic reassignment. Additionally, mitigation case studies (search‑based verification and defensive prompting) are evaluated on matched subsets, illustrating that the observed failures are not artifacts of a single prompting strategy.

7. **Human Validation** – A 14‑member, 7‑country clinician panel validates both item quality (composite score 1.76/2.00) and downstream harm (worst‑case harm in 38.2 % of reviewed cases). High inter‑rater agreement (Gwet AC2 ≥ 0.78) supports the reliability of these annotations and provides an independent check on the automatic ASR labels (98 % concordance).

Overall, the evidence chain—from large, diverse item pools, through controlled injection protocols, to multi‑model replication and human validation—is methodologically sound. The authors adequately address potential confounds, report effect sizes with confidence intervals, and provide extensive supplementary material for reproducibility. No major methodological flaws or indications of p‑hacking are evident. Consequently, the paper meets the standards for acceptance.
