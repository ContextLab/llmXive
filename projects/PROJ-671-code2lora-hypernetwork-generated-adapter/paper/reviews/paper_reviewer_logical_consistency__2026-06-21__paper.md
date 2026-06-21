---
action_items:
- id: 3f3ddc393628
  severity: fatal
  text: "The manuscript states that LoRA matrices are shared across all 28 layers\
    \ yet reports ~720\u202FM trainable parameters for the static hypernetwork. This\
    \ contradicts the parameter count implied by sharing. Re\u2011calculate and report\
    \ the correct number of trainable parameters, and ensure the description of sharing\
    \ matches the actual architecture."
- id: 65ff4d569b31
  severity: science
  text: "In the Results section, the claim that codelorastatic \u201Cmatches the per\u2011\
    repo LoRA upper bound\u201D is inconsistent with Table\u202F\\ref{tab:main_results},\
    \ where codelorastatic\u2019s IR EM (66.2\u202F%) exceeds the reported per\u2011\
    repo LoRA IR EM (64.0\u202F%). Clarify whether per\u2011repo LoRA is truly an\
    \ upper bound or adjust the claim accordingly."
- id: 3763a5cee5d7
  severity: science
  text: "The Deployment Efficiency table lists extra storage for codelorastatic as\
    \ +679\u202FMB, but a hypernetwork with ~720\u202FM parameters (even in bf16)\
    \ would require >1.4\u202FGB. Reconcile the storage figure with the actual size\
    \ of the hypernetwork and any adapter storage."
- id: 7b57d4c1d343
  severity: writing
  text: "Table\u202F\\ref{tab:ablation_data} shows a dip in CR\u2011test EM when training\
    \ on 500 repositories (61.2\u202F%) compared to 409 repositories (63.8\u202F%).\
    \ This contradicts the narrative of a log\u2011linear improvement that plateaus.\
    \ Provide an explanation or correct the table if it contains an error."
- id: 5b55c5a0e209
  severity: science
  text: The OOD evaluation caveats acknowledge that shorter target lengths inflate
    Exact Match scores, yet the paper still reports absolute EM improvements. Include
    a normalized metric (e.g., EM adjusted for target length) or discuss how this
    inflation might affect the claimed superiority.
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:45:48.674533Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: full_revision
---

The paper presents a novel hypernetwork‑generated LoRA approach for adapting code language models to repository‑level context. While the overall experimental methodology is sound, several logical inconsistencies undermine the credibility of the conclusions.

1. **Parameter Accounting vs. Architecture Description (Section 3.2 & Table \\ref{tab:main_results})**  
   The authors claim that LoRA matrices are *shared* across all 28 transformer layers, which would dramatically reduce the number of trainable weights. Yet they report ~720 M trainable parameters for the static hypernetwork and ~745 M for the evolutionary variant. This discrepancy suggests either the sharing is not implemented as described, or the parameter count is overstated. The inconsistency propagates to the storage claim in Table \\ref{tab:efficiency} (only +679 MB), which is incompatible with a 720 M‑parameter model even in bf16 (≈1.4 GB). The paper must reconcile these figures; otherwise the claim of parameter‑efficient adaptation is unsupported.

2. **Upper‑Bound Claim (Section 5.1)**  
   The static track results show codelorastatic achieving 66.2 % EM on the in‑repo (IR) test, whereas the per‑repo LoRA upper bound is reported as 64.0 % EM (Table \\ref{tab:main_results}). Stating that codelorastatic “matches” the upper bound is contradictory; it actually exceeds it. If per‑repo LoRA is not a true upper bound, the authors should re‑frame the claim (e.g., “surpasses prior per‑repo adapters”) and discuss why the hypernetwork can outperform a model trained directly on the repository.

3. **Scaling Curve Anomaly (Section A.3, Table \\ref{tab:ablation_data})**  
   The narrative describes a log‑linear improvement in CR‑test EM with increasing repository count, plateauing after ~200 repos. However, the table shows a regression at 500 repositories (61.2 % EM) compared to 409 repositories (63.8 % EM). This breaks the claimed monotonic trend and raises questions about data handling or experimental variance. The authors need to either correct the table or provide a plausible explanation (e.g., over‑fitting, data quality issues).

4. **OOD Evaluation Interpretation (Section 5.3 & Appendix \\ref{app:ood_caveats})**  
   The authors acknowledge that shorter target lengths in the OOD set inflate Exact Match scores, yet they present raw EM improvements as evidence of superiority. Without normalizing for target length or providing an alternative metric less sensitive to length (e.g., EditSim), the claim that codeloraevo “leads” may be overstated. A more rigorous analysis is required to ensure the OOD advantage is not an artifact of the evaluation design.

5. **Causal Attribution of Performance Gains**  
   The paper attributes gains primarily to the hypernetwork’s ability to embed repository knowledge into parameters. However, the ablation studies do not isolate the effect of the GRU recurrence in codeloraevo from the additional training data (commit‑derived tasks). A controlled experiment where the same amount of static data is used with a non‑recurrent hypernetwork would be needed to substantiate the causal claim that the recurrent component is responsible for the observed improvements.

Overall, the manuscript’s logical flow is compromised by these internal contradictions. Addressing the above points is essential before the paper can be accepted.
