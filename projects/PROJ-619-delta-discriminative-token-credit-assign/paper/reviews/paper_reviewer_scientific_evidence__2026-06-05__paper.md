---
action_items:
- id: 88b23d5f48db
  severity: science
  text: Clarify whether method-specific hyperparameters for SAPO/FIPO are intrinsic
    or tuned, as Section sec:exp_s claims 'same hyperparameters' but app:baseline-details
    lists unique settings.
- id: fc735678231d
  severity: science
  text: Explicitly acknowledge the limitation of single-training-seed results in the
    Limitations section, noting that RL training variance is not captured by evaluation-run-level
    significance tests.
- id: 96965ef4434c
  severity: science
  text: Provide statistical significance tests for code generation and OOD results
    (Tables tab:code_tab, tab:ood_tab) or explicitly state they are not evaluated
    to avoid overclaiming robustness.
artifact_hash: 8558369ae7497b07133b578546b356e5acc6d5d811b01a15639e1519377b2963
artifact_path: projects/PROJ-619-delta-discriminative-token-credit-assign/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T16:11:43.856023Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical results across seven mathematical benchmarks, three model scales, and code generation tasks. The ablation studies (Sections sec:own-side-main, sec:lambda-effectiveness, sec:ablation) effectively isolate the contribution of DelTA's discriminative token weighting. However, the scientific evidence regarding training stability and reproducibility requires strengthening. Section sec:exp_s and Appendix app:hyp indicate that main results are derived from a single training run per method (220 steps for 8B, 300 for 14B). While evaluation runs (16 per problem) control for inference stochasticity, RL training is notoriously sensitive to random seeds. Without multiple training seeds, the reported gains (e.g., +3.26 average points on Qwen3-8B) could partially reflect favorable initialization or rollout sampling. The Limitations section mentions proxy choices but does not explicitly address training seed variance.

Furthermore, Section sec:exp_s states that methods are "training all methods with the same hyperparameters," but Appendix app:baseline-details reveals method-specific settings for SAPO (Gae Gamma, Tau Pos) and FIPO (Decay Rate). Clarifying whether these differences are intrinsic to the baseline implementations or tuned hyperparameters is crucial for isolating the effect of the objective function. Additionally, the checkpoint selection protocol (Appendix app:hyp) optimizes for AIME25, which is included in the main average. While standard, this introduces a slight risk of overfitting to the selection metric. Finally, statistical significance is rigorously tested for the main math benchmarks (Appendix app:sig), but code generation (Table tab:code_tab) and out-of-domain results (Table tab:ood_tab) lack p-values or confidence intervals. Given the smaller effect sizes in code (47.7 to 49.5), acknowledging the uncertainty here is important. Addressing these points will solidify the claim that DelTA's improvements are robust across stochastic training trajectories.
