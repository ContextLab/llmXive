---
action_items:
- id: 86728fceab6f
  severity: science
  text: "Provide per\u2011task confidence intervals or standard errors for the reported\
    \ success rates (e.g., Table\u202F1) and describe the random seed / episode selection\
    \ procedure to allow assessment of statistical significance."
- id: 55211c0595a9
  severity: science
  text: "Include an ablation that controls for the number of trajectories used in\
    \ the data\u2011generation engine (e.g., 1\u202FK vs\u202F2\u202FK vs\u202F5\u202F\
    K) to demonstrate that performance gains are not solely due to over\u2011fitting\
    \ on a small dataset."
- id: 77ed8664cd32
  severity: science
  text: "Report the variance across runs for the RL fine\u2011tuning stage (e.g.,\
    \ multiple seeds for GRPO) to show that the observed improvements on long\u2011\
    horizon tasks are reproducible and not a result of favorable random initialization."
- id: ede71c775e08
  severity: science
  text: "Add statistical tests (e.g., paired bootstrap or permutation tests) when\
    \ comparing Guava\u2011Agent\u20114B against baselines to quantify the significance\
    \ of the reported 5\u201110\u202F% improvements."
- id: 969d05a283ec
  severity: science
  text: "Clarify how failure cases were selected for the \u2018recovery\u2019 analysis\
    \ and ensure that they are not cherry\u2011picked examples that overstate the\
    \ model\u2019s robustness."
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T00:44:35.556756Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling harness (Guava) and demonstrates that a 4 B open‑source VLM can achieve competitive manipulation performance after being distilled from frontier models using fewer than 2 K simulated trajectories. However, from a scientific‑evidence perspective several aspects of the experimental methodology limit the strength of the claims.

**Sample size and statistical reporting.** Success rates are reported for each task over 15 episodes (Table 1) without any measure of variability (e.g., standard error, confidence interval). With such a small number of trials, the observed differences (e.g., 75.6 % vs 70.2 % over GPT‑5.4) could be within random fluctuation. The paper should report per‑task variance and aggregate confidence intervals, and discuss whether the sample size provides sufficient power to detect the claimed improvements.

**Controls and ablations.** The core claim is that three design principles (iterative ReAct loops, semantic tool abstractions, multimodal observations) are essential. While Figure 3 shows ablations, the experiments do not control for the amount of data or training budget across the ablated configurations. A controlled study varying only the harness design while keeping the number of trajectories, training epochs, and random seeds constant would strengthen the causal inference.

**Replication and robustness.** The RL fine‑tuning (GRPO) is applied only to two long‑horizon tasks, and the reported gains (e.g., from 6.7 % to 60 % on “shell game”) are based on a single run. Providing results across multiple random seeds or reporting the distribution of outcomes would demonstrate that the improvements are reproducible rather than a lucky seed effect.

**Effect size and p‑hacking risk.** The paper reports many task‑level numbers but does not perform statistical tests to assess whether the observed effect sizes are significant. Without such tests, there is a risk of selective reporting (e.g., highlighting tasks where Guava‑Agent‑4B excels while downplaying failures such as “place all red objects in basket”). Including paired statistical comparisons between Guava‑Agent‑4B and each baseline would mitigate this risk.

**Alternative explanations.** The authors attribute performance gains to the harness design, yet the data‑generation engine also provides richer demonstrations (including recovery trajectories). An experiment that isolates the contribution of the harness from the data‑augmentation strategy (e.g., training the same 4 B model on a dataset without recovery trajectories) would help rule out alternative explanations.

In summary, the empirical results are promising, but the current evidence lacks sufficient statistical rigor to fully support the central claims. Addressing the points above will substantially increase confidence in the reported improvements and the generality of the Guava harness.
