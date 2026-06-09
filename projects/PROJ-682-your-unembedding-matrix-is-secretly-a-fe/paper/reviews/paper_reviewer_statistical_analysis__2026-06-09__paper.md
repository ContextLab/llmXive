---
action_items:
- id: def8465e8ccc
  severity: science
  text: Report standard deviations or confidence intervals over multiple random seeds
    for all MTEB results.
- id: 7e507b72e55e
  severity: science
  text: Correct the data inconsistency in Table 4 where PromptEOL and ECHO baselines
    are identical.
- id: c0747ea3683c
  severity: science
  text: Include statistical significance testing (e.g., paired t-tests) to validate
    reported performance gains.
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:20:44.611736Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in Section 5 lacks essential rigor required for publication. Specifically, Table 1 (lines 300-330) reports point estimates for MTEB scores without standard deviations or confidence intervals across multiple random seeds. Given the marginal improvements (e.g., +0.1% on Retrieval for Llama), the absence of significance testing (e.g., paired t-tests or bootstrap resampling) makes it impossible to distinguish signal from noise. The claim of "superior performance" is statistically unsupported without variance metrics. 

Additionally, Table 4 (lines 620-640) exhibits a critical data integrity issue: the baseline scores for "PromptEOL" and "ECHO" are identical (70.43, 68.80, etc.), which contradicts the distinct mechanisms described in Section 2.2 and prior literature. This suggests a copy-paste error that invalidates the comparative analysis in that table. Furthermore, the "Avg." metric calculation is ambiguous; it is unclear if the 49 datasets (Section 5.1) are weighted equally or by task volume, affecting the interpretation of the aggregate gain. 

Finally, the ablation study (Table 5, lines 650-670) tests multiple filtering strategies ($\tau=2,4,8$) without correcting for multiple comparisons. To support claims of robustness, the authors must report variance over at least three seeds, apply significance testing for reported gains, and rectify the data inconsistencies in Table 4. Without these corrections, the statistical evidence does not substantiate the proposed method's efficacy over existing baselines.
