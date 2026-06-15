---
action_items:
- id: 9aa6559e8ec8
  severity: writing
  text: Align abstract claim of 'up to 5.8x throughput speedup under SGLang' with
    provided Table 2 (high_concurrency.tex), which shows a maximum of 5.1x. Either
    update the text to match the data or provide the missing benchmark configuration.
- id: ac314d7e05fd
  severity: writing
  text: Qualify the claim 'Domino consistently outperforms... DFlash' in the Introduction
    (sec/2introduction.tex), as Table 1 (main_result.tex) shows DFlash outperforming
    Domino on Qwen3-4B T=1 AIME25 (3.79x vs 3.75x).
artifact_hash: ac9b2293924c2f0c1f04178796bb698ee01d07baef5d80d5250c3c91d8a5b9a5
artifact_path: projects/PROJ-654-https-arxiv-org-abs-2605-29707/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T00:57:41.322547Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a well-motivated approach to speculative decoding, but there are instances where the textual claims overreach the specific data presented in the provided LaTeX artifacts.

First, the Abstract states: "Domino achieves... up to 5.8x throughput speedup under SGLang serving." However, the provided `latex/table/high_concurrency.tex` (Table 2) does not support this maximum value. The highest reported speedup in that table is 5.1x (Qwen3-8B GSM8K, Concurrency 2). This discrepancy suggests either an unreported experiment or an overstatement in the abstract. As a reviewer, I must rely on the provided evidence; claiming a specific metric not present in the results section constitutes overreach. Please align the abstract with the data in `high_concurrency.tex` or include the missing benchmark configuration in the appendix.

Second, the Introduction (sec/2introduction.tex) asserts that "Domino consistently outperforms EAGLE-3, DART, and DFlash." While the average speedup is higher, "consistently" implies uniform superiority across all reported benchmarks. Table 1 (`latex/table/main_result.tex`) shows that DFlash outperforms Domino on Qwen3-4B with Temperature=1 on the AIME25 benchmark (3.79x vs 3.75x). While this is a marginal difference, the absolute claim of "consistently" is technically unsupported by the full result matrix. Softening this to "generally outperforms" or "achieves higher average speedup" would be more accurate.

On a positive note, the Limitations section is honest about hardware dependencies and framework compatibility, which mitigates overreach in deployment claims. The training strategy ablation (sec/6experiment.tex) is also well-grounded in the provided figures. However, the numerical claims in the Abstract and Introduction require tightening to match the provided tables to ensure scientific rigor.
