---
action_items:
- id: 6a1446dd88a2
  severity: science
  text: "Provide statistical significance testing (e.g., confidence intervals, hypothesis\
    \ tests, or bootstrapped variance) for all reported success\u2011rate improvements\
    \ (LIBERO\u2011PRO, MolmoSpaces, RoboSuite, and real\u2011world). The current\
    \ tables only show point estimates, making it unclear whether the gains are robust."
- id: ccade87f3cab
  severity: science
  text: "Report the number of random seeds or environment initializations used per\
    \ task beyond the fixed trial counts (e.g., are the 10 initializations per LIBERO\u2011\
    PRO task drawn from a single seed set?). Include variance across seeds to assess\
    \ reproducibility."
- id: 22f9c2bbd403
  severity: science
  text: "Clarify the total token/computational budget allocated to the play phase\
    \ versus test\u2011time inference, and justify that the observed gains are not\
    \ merely due to increased compute (address the compute\u2011matched comparison\
    \ more rigorously)."
- id: 9feaccd134bd
  severity: science
  text: Include ablations that control for potential confounds such as the effect
    of longer retry budgets, different LLM models, or variations in the curiosity
    reward formulation. This will help rule out alternative explanations for the performance
    boost.
- id: d4addd3f457d
  severity: science
  text: "For the real\u2011world evaluation (80 trials total), perform statistical\
    \ analysis (e.g., binomial confidence intervals) and discuss whether the observed\
    \ 8.8\u202Fpp gain is statistically meaningful given the small sample size."
artifact_hash: 50abfa42bd37b77889e3563a6ea1bdb0e8be3fa0ecf45caffb5d23cfc888d2a4
artifact_path: projects/PROJ-749-playful-agentic-robot-learning/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T15:38:47.240284Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents an intriguing framework—RATs—for self‑directed play‑driven skill acquisition in Code‑as‑Policy agents. Empirically, it reports sizable percentage‑point improvements across several simulated benchmarks (e.g., LIBERO‑PRO average success ↑ 20.6 pp, MolmoSpaces ↑ 17.0 pp) and modest gains in real‑world trials. However, the scientific evidence supporting these claims is under‑specified:

1. **Sample Sizes & Variability** – While trial counts are listed (e.g., 600 LIBERO‑PRO trials, 400 MolmoSpaces trials), the paper does not report variability (standard deviations, confidence intervals) or statistical significance. Without such measures, it is impossible to assess whether the observed differences could arise from random fluctuations.

2. **Multiple Comparisons & p‑hacking Risk** – The authors evaluate many conditions (object/goal/spatial splits, several baselines, ablations, and two test‑time systems). No correction for multiple hypothesis testing is described, raising the risk of over‑interpreting chance improvements.

3. **Compute Budget Confounds** – The “compute‑matched” analysis (Table 9) attempts to isolate the effect of play‑time compute, but the methodology (amortizing token counts, adjusting retry budgets) is described only qualitatively. A more rigorous accounting (e.g., equalizing total FLOPs or wall‑clock time) is needed to rule out that the gains stem from extra inference rather than the learned skill library.

4. **Real‑World Evaluation Robustness** – The real‑world experiments involve only 80 trials (two tasks). The reported 8.8 pp increase lacks any statistical assessment, making it unclear whether the improvement is reliable or could be due to sampling noise.

5. **Ablation Depth** – The ablation tables (e.g., Table 5) show that “Curious Play” improves performance, but they do not explore sensitivity to the curiosity hyperparameters (e.g., weighting of novelty vs. competence) or to the number of play iterations. Such analyses would strengthen the claim that the specific play‑strategy, rather than any form of additional data, drives the gains.

6. **Reproducibility Details** – Key experimental details (random seed handling, exact LLM prompts, token limits per turn) are relegated to the appendix. For rigorous evaluation, these should be summarized in the main text and made publicly available (e.g., via a repository) to enable independent replication.

In summary, the paper’s central empirical claims are promising but lack the statistical rigor and thorough control analyses required for a strong scientific contribution. Addressing the points above would substantially improve the evidential foundation of the work.
