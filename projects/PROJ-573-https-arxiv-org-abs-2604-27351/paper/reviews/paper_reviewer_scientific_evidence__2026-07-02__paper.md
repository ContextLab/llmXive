---
action_items:
- id: 6fbcef755748
  severity: science
  text: The benchmark size (N=200) is critically small for claiming 'extensive experiments'
    across 9 sub-domains and 3 modalities. With only ~22 samples per sub-domain, statistical
    significance of the reported ~6-7% utility gains is unverifiable without confidence
    intervals or p-values. The paper must report variance metrics (std dev) and statistical
    tests to support the claim that gains are not due to sampling noise.
- id: 29e8c8085b83
  severity: science
  text: The 'Single-LLM-Agent' baseline uses gpt-5-nano, but the text mentions evaluating
    'other models from and beyond the GPT family' without presenting comparative data
    for non-GPT baselines in the main tables. To validate the claim that Eywa improves
    over 'language-only baselines' generally, results for at least one non-GPT baseline
    (e.g., Gemini or Claude) must be included in Table 1.
- id: 1c2150d6683f
  severity: science
  text: The theoretical claim of 'strict risk improvement' (Theorem 1) relies on Assumption
    2 (Domain Advantage), which posits that FMs strictly outperform LLMs on serialized
    inputs. The empirical section does not explicitly validate this assumption by
    comparing the raw performance of Chronos/TabPFN against the LLM on the serialized
    inputs in isolation. A dedicated ablation showing the FM-only vs. LLM-only performance
    on the domain-specific component is required to ground the theoretical claims.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:39:19.526832Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the central claims of the Eywa framework is currently insufficient to justify the strong assertions of "strict improvement" and "extensive evaluation."

**Sample Size and Statistical Rigor:**
The primary experimental evaluation relies on `EywaBench-V1`, which the authors explicitly state consists of only **200 task instances** (Appendix, `1_appendix/data_analysis.tex`, Section "EywaBench-V1"). This sample size is distributed across three parent domains and nine sub-domains, resulting in approximately 22 samples per sub-domain. The main results table (`tables/main_comparison_eywabench.tex`) reports mean utility improvements of ~6.6% for `EywaAgent` and ~6% for `EywaMAS` over baselines. However, the manuscript **fails to report standard deviations, confidence intervals, or p-values** for these metrics. With such a small N, the observed gains could easily be artifacts of sampling variance rather than genuine methodological improvements. The claim of "extensive experiments" is scientifically unsupported given the limited data volume.

**Baseline Validity:**
The paper claims to evaluate against "single-agent LLM baselines" including Gemini and Claude families (`0_sections/5_experiment.tex`, Section "Baseline methods"). However, Table 1 (`tables/main_comparison_eywabench.tex`) only presents results for the `Single-LLM-Agent` (identified as gpt-5-nano in the text). There is no empirical evidence provided for the performance of Gemini or Claude on this benchmark. Without these results, the claim that Eywa outperforms "language-only baselines" generally is an overreach; the evidence only supports superiority over a specific GPT-5-nano configuration.

**Theoretical-Empirical Alignment:**
Theorem 1 (`0_sections/3_eywaagent.tex`) asserts a "strict risk improvement" based on Assumption 2 (Domain Advantage), which posits that domain-specific FMs strictly outperform LLMs on serialized inputs. The experimental section does not isolate this variable. There is no direct comparison showing the raw performance of Chronos or TabPFN against the LLM on the *serialized* domain-specific inputs alone. Without this ablation, the assumption remains unverified, and the theoretical guarantee lacks empirical grounding. The case studies (Appendix) are qualitative and do not substitute for quantitative validation of the core assumption.

**Recommendation:**
The authors must expand the benchmark to a statistically significant size (e.g., N > 1000) or, at minimum, provide rigorous statistical analysis (bootstrapped confidence intervals) for the current N=200. Additionally, the missing baseline results and the unverified domain advantage assumption must be addressed to substantiate the paper's central claims.
