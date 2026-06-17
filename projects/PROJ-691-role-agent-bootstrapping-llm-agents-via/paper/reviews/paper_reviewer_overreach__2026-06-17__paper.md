---
action_items:
- id: 483eade6ff7e
  severity: writing
  text: "Temper the blanket claim that Role-Agent \u201Cconsistently outperforms existing\
    \ approaches\u201D by acknowledging the observed under\u2011performance on the\
    \ NQ single\u2011hop QA benchmark (Table\u202F2) and any other cases where baselines\
    \ are competitive."
- id: c8daa077163d
  severity: science
  text: "Provide a more rigorous analysis of the predictive reward formulation (multiplicative\
    \ modulation). Discuss whether this design could still introduce bias or enable\
    \ reward\u2011hacking, especially in trajectories with low task reward but high\
    \ predictive alignment."
- id: 7cc23bae108d
  severity: science
  text: "Justify the choice of the state\u2011similarity threshold (0.9) used for\
    \ state grouping. Include an ablation or sensitivity study showing the impact\
    \ of varying this threshold on performance and generalisation across tasks."
artifact_hash: 3eaf93f21c39f248e829c853cd8d9efc8318a737e9dbae23f33fdd68c6c59724
artifact_path: projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T00:45:19.268407Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript presents an ambitious dual‑role framework (World‑In‑Agent and Agent‑In‑World) and reports impressive gains on several text‑based benchmarks. However, the claim of “consistent” superiority over all baselines is not fully supported: in Table 2 the Role‑Agent model lags behind GiGPO on the NQ single‑hop QA set, and the text does not acknowledge this exception. This over‑generalisation could mislead readers about the method’s robustness across domains.

Moreover, the predictive reward is introduced as a purely modulatory factor (multiplication by 1 + R_pre), yet the paper does not analyze possible side‑effects. Even with multiplication, high predictive scores can amplify small task rewards, potentially rewarding agents for accurate predictions on otherwise failed trajectories. A brief discussion or empirical check for such reward‑hacking would strengthen the scientific validity.

Finally, the state‑grouping mechanism relies on a fixed longest‑matching subsequence similarity threshold of 0.9, inherited from prior work. The manuscript notes that this “limits cross‑task generalisation” in the limitations section, but it provides no empirical evidence. Including a sensitivity experiment (e.g., thresholds 0.7–0.95) would clarify whether the chosen value is optimal or inadvertently restricts the method’s applicability.

Addressing these points will align the paper’s claims with the presented evidence and improve the rigor of the contribution.
