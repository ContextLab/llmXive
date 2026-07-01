---
action_items:
- id: ff5f9bf01f73
  severity: science
  text: The paper lacks statistical significance testing for the reported performance
    gains. With only 150 training steps and single-run reporting (no seeds mentioned),
    claims of 'consistent improvements' (e.g., +9.3 on ALFWorld) are not robust. Provide
    standard deviations over multiple seeds or confidence intervals to rule out variance-driven
    results.
- id: ff8539b152b2
  severity: science
  text: 'The ''analyzer'' (GLM-5.2) used for skill extraction is a proprietary, closed-source
    model not available for independent verification. This introduces a ''black box''
    confounder: the gains may stem from the analyzer''s specific reasoning biases
    rather than the OPID mechanism. Reproduce skill extraction with an open-source,
    reproducible model or provide the exact prompt and analyzer outputs for all trajectories.'
- id: 8f895bc5790e
  severity: science
  text: The ablation study on 'Critical-First Skill Routing' (Table 2) shows a +6.8
    point gain, but the 'w/o Routing' baseline (77.5) is not clearly defined. Does
    it use random routing, uniform averaging, or always episode-level? The experimental
    design must explicitly define the counterfactual to validate the routing hypothesis.
- id: 04986e5c0287
  severity: science
  text: Sample efficiency claims (Fig 3) rely on a single curve without error bars.
    The claim that OPID 'surpasses full-data GRPO' at 80% data (78.9 vs 75.0) is highly
    sensitive to random initialization and data sampling. Provide a learning curve
    with multiple seeds to confirm this non-monotonic behavior is not an artifact
    of a lucky seed.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:04:26.927172Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of OPID is currently insufficient due to a lack of statistical rigor and reproducibility controls. While the methodological design is sound, the empirical validation relies heavily on single-run results without reported variance, making it impossible to distinguish genuine algorithmic improvements from stochastic noise.

**1. Lack of Statistical Significance and Replication**
The paper reports specific point improvements (e.g., +9.3 on ALFWorld, +26.5 on WebShop) in Section 3.2 and Table 1. However, the "Implementation Details" (Section 3.1) state models are trained for 150 steps but do not mention the number of random seeds used. In reinforcement learning, especially with sparse rewards and small batch sizes (16 for ALFWorld), performance can vary significantly across seeds. Without reporting mean and standard deviation over at least 3-5 seeds, the claim that OPID "consistently strengthens" outcome-only RL is unsupported. The training dynamics in Figure 2 and sample efficiency in Figure 3 are presented as single curves, which is insufficient to validate the robustness of the proposed advantage function.

**2. The "Black Box" Analyzer Confounder**
The core innovation relies on an LLM-based analyzer (identified as GLM-5.2 in Appendix A.2) to extract "hindsight skills." This introduces a significant confounding variable. The performance gains could be attributed to the specific reasoning capabilities or biases of the GLM-5.2 model rather than the OPID distillation mechanism itself. Since GLM-5.2 is a proprietary model (implied by the citation format and lack of open weights), the experiment cannot be independently reproduced. The authors must either:
a) Release the exact prompts and the full set of extracted skills for all trajectories to allow re-evaluation.
b) Replicate the experiment using a fully open-source, reproducible analyzer (e.g., a smaller open LLM) to demonstrate that the gains are not dependent on a specific proprietary model's "intelligence."

**3. Ambiguity in Ablation Baselines**
The ablation study on "Critical-First Skill Routing" (Table 2) compares OPID (84.3) against a "w/o Routing" variant (77.5). The text does not explicitly define the behavior of the "w/o Routing" baseline. Does it apply step-level skills everywhere? Episode-level everywhere? Or a random mixture? Without a precise definition of the counterfactual, the +6.8 point gain cannot be definitively attributed to the routing logic. The experimental setup must be clarified to ensure the ablation isolates the routing mechanism correctly.

**4. Overfitting to Specific Data Splits**
The sample efficiency analysis (Section 3.3, Table 4) claims OPID surpasses full-data GRPO when using only 80% of the data. This counter-intuitive result (better performance with less data) is a strong claim that requires rigorous validation. It is highly susceptible to overfitting on a specific random subset of the training data. The authors must provide learning curves with error bars across multiple random data splits to confirm this is a genuine property of the algorithm and not a statistical fluke.

In summary, the paper presents a promising framework but fails to provide the statistical evidence required to validate its claims. The reliance on a single run, a proprietary analyzer, and ambiguous ablation baselines prevents a robust assessment of the method's scientific validity.
