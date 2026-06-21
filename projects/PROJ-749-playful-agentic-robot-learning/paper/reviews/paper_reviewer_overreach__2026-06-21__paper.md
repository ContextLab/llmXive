---
action_items:
- id: 354a231afdba
  severity: science
  text: "The manuscript overstates the generality of the reported gains. Claims such\
    \ as \u201Cplay\u2011learned skills improve downstream performance both within\
    \ the full RATs system and as a plug\u2011and\u2011play addition to other inference\u2011\
    time Code\u2011as\u2011Policy methods\u201D are not supported by extensive cross\u2011\
    domain or cross\u2011embodiment evaluations; only a handful of RoboSuite tasks\
    \ and two real\u2011world tasks were tested."
- id: 9a09b7923af9
  severity: science
  text: "The reported real\u2011world improvements (\u22488\u20139\u202Fpp) are based\
    \ on very limited experiments (2 tasks, 40 trials each) and lack statistical significance\
    \ analysis. The paper should temper statements like \u201Cplay\u2011learned code\
    \ skills can be reused on real hardware for simple manipulation tasks\u201D or\
    \ provide broader real\u2011world validation."
- id: 44ed13ee5986
  severity: writing
  text: "The comparison to a compute\u2011matched CaP\u2011Agent0 baseline (Table\u202F\
    9) shows that most of the performance boost comes from the learned skill library\
    \ rather than the extra compute during play. The claim that \u201Cwithout finetuning\
    \ the underlying model\u201D the system achieves large gains is therefore misleading\
    \ and should be qualified."
- id: d9b1d9a05313
  severity: science
  text: "Cross\u2011embodiment transfer (e.g., two\u2011arm lifting) is demonstrated\
    \ on a single RoboSuite task with a modest success increase. The paper should\
    \ avoid broad statements about cross\u2011embodiment applicability until more\
    \ diverse multi\u2011arm or different robot platforms are evaluated."
- id: 7a7b9ff39bd9
  severity: writing
  text: "The abstract and conclusion present percentage\u2011point improvements (20.6\u202F\
    pp, 17.0\u202Fpp) as if they are universally significant, but the baselines (e.g.,\
    \ CaP\u2011Agent0) are relatively weak and the evaluation budget (10 trials per\
    \ task) is small. The authors should contextualize these gains and discuss variability."
artifact_hash: 50abfa42bd37b77889e3563a6ea1bdb0e8be3fa0ecf45caffb5d23cfc888d2a4
artifact_path: projects/PROJ-749-playful-agentic-robot-learning/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T15:38:28.000464Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper introduces **RATs**, a framework for “playful agentic robot learning,” and reports notable percentage‑point improvements on simulated benchmarks (LIBERO‑PRO, MolmoSpaces) and modest gains on a few RoboSuite and real‑world tasks. While the idea of self‑directed play for skill acquisition is compelling, several claims extend beyond what the presented data substantiate.

1. **Scope of Generalization** – The manuscript repeatedly asserts that the learned skill library provides a “practical, plug‑and‑play mechanism” that improves any downstream Code‑as‑Policy system without finetuning. However, the only cross‑domain evidence consists of a single RoboSuite benchmark (Table 7) and two real‑world tasks (Table 10). This limited set does not justify broad generality claims, especially given the variability inherent in real‑world manipulation.

2. **Real‑World Validation** – Real‑world experiments involve only two task types (cube pick‑and‑place, drawer closing) with 40 trials each, yielding modest absolute success rates (≈30–40 %). No statistical analysis (e.g., confidence intervals) is provided, making it unclear whether the observed ~8 pp improvement is significant. The paper should either expand the real‑world evaluation or temper the language describing real‑world applicability.

3. **Compute‑Matched Baseline** – Section 5.5 (Table 9) shows that allocating the same token budget to a stronger CaP‑Agent0 at test time yields only a small gain (23.2 % → 26.0 %). This suggests that much of the reported improvement stems from the skill library rather than the extra compute during play. The claim that “without finetuning the underlying model” the system achieves large gains is therefore misleading and should be qualified.

4. **Cross‑Embodiment Claims** – The two‑arm lifting result (Table 7) is based on a single RoboSuite task, yet the paper suggests that play‑learned skills “transfer across embodiments.” More diverse multi‑arm or different robot platforms are needed before such a claim can be justified.

5. **Statistical Significance and Variability** – All benchmark results are based on 10 trials per task (or 5 for the full‑system ablation). The paper does not report variance, confidence intervals, or statistical tests, which are essential for interpreting the reported 20.6 pp and 17.0 pp gains. Without this, the magnitude of improvement may be overstated.

6. **Baseline Strength** – The primary baseline, CaP‑Agent0, is a relatively simple Code‑as‑Policy agent. Comparing against stronger baselines (e.g., recent vision‑language‑action models) would provide a more realistic assessment of the contribution of play‑learned skills.

**Recommendations**:  
- Re‑phrase claims to reflect the limited scope of the experiments (e.g., “demonstrated improvements on selected simulated and real‑world tasks”).  
- Include statistical analysis (standard deviations, confidence intervals) for all reported success rates.  
- Expand real‑world evaluation to more tasks, objects, and robot platforms, or clearly state the current limitations.  
- Provide additional baselines or a more thorough compute‑matched analysis to isolate the effect of the skill library versus extra inference compute.  
- Clarify that cross‑embodiment transfer is demonstrated on a single task and is an initial observation rather than a proven capability.
