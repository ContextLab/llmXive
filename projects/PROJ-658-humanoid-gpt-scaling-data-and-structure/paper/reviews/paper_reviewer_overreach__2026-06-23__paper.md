---
action_items:
- id: dd8d217c3665
  severity: science
  text: "The manuscript repeatedly claims *unprecedented* zero\u2011shot generalisation\
    \ (e.g., abstract line\u202F1, Table\u202F1, and Sec.\u202F4) without providing\
    \ statistically\u2011significant comparisons to strong baselines on a sufficiently\
    \ diverse set of unseen tasks; add rigorous zero\u2011shot benchmarks (e.g., additional\
    \ motion families, cross\u2011dataset tests) and report variance/ confidence intervals."
- id: 6391d097cbdc
  severity: science
  text: "The paper states that scaling to 2\u202FB frames *materially improves* tracking\
    \ and that a scaling law is derived (Sec.\u202F5), yet no quantitative fit (exponent,\
    \ R\xB2) or ablation isolating data\u2011scale vs. model\u2011scale is presented;\
    \ include a formal scaling\u2011law analysis with fitted curves and error bars."
- id: 469f178cd1b7
  severity: science
  text: "Claims such as \u201Cfirst systematic evidence that video\u2011estimated\
    \ motion can materially improve tracking\u201D (Sec.\u202F1) are unsupported because\
    \ no ablation comparing video\u2011estimated vs. purely mocap data is shown; provide\
    \ a controlled experiment isolating this factor."
- id: b00b244ecf33
  severity: science
  text: "The statement that the method \u201Cestablishes a new performance frontier\u201D\
    \ (abstract and Sec.\u202F4) is overstated given that the evaluation metrics (e.g.,\
    \ MPJPE, SR) are reported without statistical significance testing against baselines;\
    \ add appropriate statistical tests (e.g., paired t\u2011test) and discuss practical\
    \ significance."
- id: 6ed30b55b536
  severity: writing
  text: "The paper asserts that the model \u201Cmaintains real\u2011time performance\u201D\
    \ (Sec.\u202F4.3) based on a single latency figure; however, latency is only measured\
    \ on a high\u2011end RTX\u202F4090 and does not reflect deployment on typical\
    \ robot hardware; report latency on the target robot\u2019s compute platform and\
    \ discuss any trade\u2011offs."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:59:09.034766Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the evidence presented, which risks misleading readers about the true capabilities of Humanoid‑GPT.  

1. **Zero‑shot generalisation** – Throughout the abstract, Table 1, and Sec. 4 the authors claim “unprecedented zero‑shot generalisation” to unseen motions. The experimental section only evaluates four dance clips (Table 2) and a limited set of simulated motions. No statistical analysis (e.g., confidence intervals, significance testing) is provided, and the baselines (GMT, TWIST, Any2Track) are not evaluated on the same zero‑shot protocol. This overstates the generality of the method.  

2. **Scaling law** – Sec. 5 presents a qualitative scaling trend (Fig. 6, Fig. 7) but does not fit a quantitative law (e.g., power‑law exponent, R²) nor separate the contributions of data size versus model capacity. Without a formal fit, the claim that a “scaling law” governs performance is unsubstantiated.  

3. **Video‑estimated motion benefit** – The introduction (lines 30‑35) claims that video‑estimated motion “materially improves tracking” when scaled, yet the paper never includes an ablation that removes the video‑derived data or compares against a purely mocap‑only corpus. This makes the claim speculative.  

4. **Performance frontier** – The statement that the method “establishes a new performance frontier” (abstract and Sec. 4) is not backed by rigorous statistical comparison. Reported improvements (e.g., MPJPE reductions) are modest and lack variance estimates, making it unclear whether they are practically significant.  

5. **Real‑time inference** – Latency results (Fig. 5) are measured on an RTX 4090 GPU, which is far more powerful than the compute typically available on a Unitree‑G1 robot. The claim of “real‑time performance” therefore does not reflect realistic deployment constraints.  

To align the manuscript with its claims, the authors should (a) expand zero‑shot evaluation to a broader, statistically‑validated set of motions; (b) provide a formal scaling‑law fit with clear separation of data and model effects; (c) include an ablation isolating video‑estimated data; (d) report statistical significance for all performance gains; and (e) benchmark inference latency on the actual robot hardware. Addressing these points will ensure that the paper’s conclusions are properly supported by the presented evidence.
