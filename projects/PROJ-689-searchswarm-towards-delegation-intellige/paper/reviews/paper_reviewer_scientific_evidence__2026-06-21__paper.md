---
action_items:
- id: 5b6dd254ef0b
  severity: science
  text: "Provide statistical significance testing (e.g., confidence intervals or p\u2011\
    values) for all reported benchmark scores in Table\u202F1 (Sec\u202F4.2) and Table\u202F\
    2 (Sec\u202F4.6) to demonstrate that observed gains are not due to random variation."
- id: 50a746961cd7
  severity: science
  text: "Report the number of random seeds, training runs, and any variance (standard\
    \ deviation or inter\u2011quartile range) for the main results; currently only\
    \ a single point estimate is shown, which hampers assessment of reproducibility."
- id: 355ba936d133
  severity: science
  text: "Clarify the exact size of the SFT dataset (number of trajectories, total\
    \ token count) and the proportion retained after filtering; without this, the\
    \ claim of \u201Chigh\u2011quality\u201D data lacks quantitative backing."
- id: f79911f93722
  severity: science
  text: "Explain how baseline models were evaluated under comparable conditions (e.g.,\
    \ whether context\u2011management was enabled for all baselines); the asterisk\
    \ notation in Table\u202F1 suggests inconsistent settings."
- id: 4134f0683afd
  severity: science
  text: "Include an ablation that controls for the effect of the harness versus simply\
    \ increasing model capacity (e.g., fine\u2011tune a different 30B model without\
    \ the harness on the same data) and report statistical differences."
- id: 856a782b9d09
  severity: science
  text: "Add a replication study or cross\u2011validation on a held\u2011out subset\
    \ of the benchmarks to demonstrate that the reported improvements generalize beyond\
    \ the specific test sets used."
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:49:26.510823Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents an ambitious system (SearchSwarm) that augments a 30 B LLM with a delegation harness and reports strong performance gains on four browsing benchmarks (BrowseComp, BrowseComp‑ZH, GAIA, xbench‑DeepSearch‑2505) and several open‑ended research tasks. While the engineering contributions are clear, the scientific evidence supporting the central claims is insufficiently quantified.

1. **Sample Size and Dataset Transparency** – The SFT data collection (Sec 3.1) mentions “queries from RedSearcher and OpenSeeker” but never states how many distinct queries, total trajectories, or token volume were generated. Without these numbers, the claim that the harness yields “high‑quality delegation” cannot be evaluated for statistical power.

2. **Lack of Replication and Variance Reporting** – All benchmark scores in Table 1 (Sec 4.2) and Table 2 (Sec 4.6) are presented as single point values with an asterisk indicating context‑management. No standard deviations, confidence intervals, or results across multiple random seeds are provided. This makes it impossible to assess whether the observed improvements (e.g., +10.0 on BrowseComp over the base harness) are robust or could be due to stochastic training variance.

3. **Control Conditions and Fair Baseline Comparison** – The baselines include a mixture of closed‑source and open‑source models, some of which are evaluated with context‑management enabled (asterisk) while others are not. The manuscript does not explain why certain baselines receive this advantage and others do not, raising concerns about an uneven playing field. A controlled experiment where all models are evaluated under identical settings is needed.

4. **Effect Size and Statistical Significance** – The reported gains (e.g., SearchSwarm 68.1 vs. Tongyi DeepResearch 43.4 on BrowseComp) are large in absolute terms, but without statistical testing we cannot rule out that they stem from over‑fitting to the specific benchmark splits. Reporting p‑values or non‑parametric tests would substantiate the claim of “state‑of‑the‑art” performance.

5. **Ablation Scope** – The harness ablation (Sec 4.3) uses only 200 BrowseComp questions, which is a modest sample relative to the full benchmark. Moreover, the ablation does not include a control where a different 30 B model is fine‑tuned on the same data without the harness, limiting the ability to isolate the contribution of the harness versus model capacity.

6. **Generalization Claims** – The open‑ended research evaluation (Table 2) mixes heterogeneous tasks (ScholarQA‑v2, HealthBench, etc.) but again provides only point estimates. No analysis of variance across task domains is offered, making the claim that “delegation‑learned reasoning benefits even without subagents” less convincing.

In summary, the paper would benefit from a more rigorous experimental methodology: explicit reporting of dataset sizes, multiple training runs with variance measures, statistically sound comparisons across all baselines, and broader replication tests. Addressing these points will substantially strengthen the evidential basis for the claimed delegation intelligence.
