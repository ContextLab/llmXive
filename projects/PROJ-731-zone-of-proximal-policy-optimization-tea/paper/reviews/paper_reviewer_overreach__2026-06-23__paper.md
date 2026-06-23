---
action_items:
- id: 162a5773b697
  severity: writing
  text: "The abstract states a +9.3\u202Fpp gain for the 0.8\u202FB VLM benchmark,\
    \ but Table\u202F1 shows the actual improvement is +7.9\u202Fpp (33.1\u202F% vs\
    \ 25.2\u202F%). Align the numeric claim with the reported results."
- id: 5af0790ac2f5
  severity: writing
  text: "The manuscript claims ZPPO \u201Cresolves\u201D the brittleness of distillation\
    \ and the on\u2011policy drift problem. This is an over\u2011strong conclusion\
    \ given the evidence is limited to a set of benchmarks and does not demonstrate\
    \ broader generalization or theoretical guarantees. Re\u2011phrase to a more modest\
    \ claim about empirical improvement."
- id: 5a78bff1b1a5
  severity: writing
  text: "The paper reports that 9\u202FB students \u201Capproach\u201D the 27\u202F\
    B teacher within \u22641\u202Fpp on several benchmarks, yet the overall macro\u2011\
    average gap remains >30\u202Fpp (teacher LLM\u202FAvg\u202F71.8\u202F% vs student\
    \ 33.1\u202F%). Provide a clearer statement of the specific benchmarks where the\
    \ gap is \u22641\u202Fpp, and avoid implying near\u2011parity overall."
- id: ee3169281824
  severity: science
  text: "Statistical significance is presented for some ablations (bootstrap CIs)\
    \ but not for the primary claim that ZPPO outperforms all baselines across every\
    \ benchmark block. Add significance testing (e.g., paired bootstrap) for the main\
    \ comparison to substantiate the universal positive \u0394 claim."
- id: ab18ed94b7dd
  severity: science
  text: "The discussion of \u201Csuper\u2011additive\u201D gains from combining replay\
    \ and reformulations lacks a quantitative decomposition of interaction effects.\
    \ Include an explicit analysis (e.g., interaction term in ANOVA) to support the\
    \ super\u2011additivity assertion."
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:02:48.623759Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper introduces Zone of Proximal Policy Optimization (ZPPO), a method that moves teacher knowledge from gradient‑based distillation into the prompt via Binary Candidate‑included Questions (BCQ) and Negative Candidate‑included Questions (NCQ), coupled with a prompt replay buffer. While the experimental section is extensive, several statements extend beyond what the presented data justify.

1. **Numeric inconsistency** – The abstract advertises a “+9.3 pp” improvement for the 0.8 B VLM benchmark, yet Table 1 (lines ≈ 120‑130) reports 33.1 % for ZPPO versus 25.2 % for the base, a gain of +7.9 pp. This discrepancy suggests an over‑claim that must be corrected.

2. **Over‑generalized solution claim** – The introduction (Sec 1, lines ≈ 5‑10) and conclusion (Sec 6) assert that ZPPO “resolves” the brittleness of logit‑matching distillation and the on‑policy drift caused by teacher‑prefix RL. The evidence consists of benchmark averages on a specific set of 31 tasks; no theoretical analysis or broader generalization study is provided. The language should be softened to reflect that ZPPO *mitigates* these issues in the evaluated settings rather than fully solving them.

3. **Teacher‑student gap framing** – Section 8 (teacher capability) shows the 27 B teacher achieving 71.8 % LLM average, while the best student (9 B) reaches 33.1 % (Table 13). The claim that 9 B students “approach” the teacher within ≤1 pp is true only for a handful of benchmarks, but the manuscript does not specify which ones, potentially misleading readers about overall parity. A precise enumeration of the benchmarks where the gap is ≤1 pp is needed, and the broader gap should be acknowledged.

4. **Statistical support for primary claim** – The paper supplies bootstrap confidence intervals for ablation deltas (Appendix C, Table 30) but does not present comparable significance testing for the headline comparison (ZPPO vs. GRPO † across all 31 benchmarks). Without paired significance tests, the universal positive Δ claim (Sec 4.2) is not fully substantiated.

5. **Super‑additive effect justification** – The narrative (Sec 4.3, “super‑additive gains”) suggests that replay × reformulation yields more than the sum of its parts. However, the presented tables only show additive differences; no interaction analysis is offered. An explicit statistical interaction test would strengthen this claim.

6. **Scope of evaluation** – All experiments are confined to the Qwen 3.5 family and a proprietary 77 k multimodal RL corpus (Appendix A). The paper extrapolates the benefits of ZPPO to “compact VLMs” in general, but no cross‑model or cross‑dataset validation is provided. This limits the generality of the conclusions.

Overall, the manuscript presents promising empirical results, but several claims overstate the evidence. Addressing the points above—especially correcting the abstract figure, tempering absolute language, clarifying teacher‑student gap statements, and adding statistical validation—will bring the paper’s conclusions into alignment with its data.
