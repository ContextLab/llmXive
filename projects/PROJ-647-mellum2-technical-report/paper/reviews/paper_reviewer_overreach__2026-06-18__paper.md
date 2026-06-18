---
action_items:
- id: 3e40108c62ea
  severity: fatal
  text: "Correct the claim that Mellum\u202F2 attains the best MMLU\u2011Pro score\
    \ (Table\u202F\\ref{tab:posttrain-eval-instruct} shows 78.1\u202F% vs 91.1\u202F\
    % for Qwen3.5\u20119B)."
- id: d34e5fd4abc6
  severity: writing
  text: "Clarify the latency vs throughput statements: the paper says Mellum\u202F\
    2 \u201Cmatches Qwen2.5\u20117B\u2019s latency\u201D (Fig.\u202F\\ref{fig:throughput-comparison})\
    \ but also claims it \u201Cmatches \u2026 throughput\u201D while the figure shows\
    \ a 21\u202F% higher throughput. Re\u2011phrase to avoid contradictory over\u2011\
    claims."
- id: 0528ffbfcc47
  severity: science
  text: "Provide concrete evidence that Mellum\u202F2 runs at the per\u2011token compute\
    \ of a 2.5\u202FB dense model (e.g., FLOPs or GPU\u2011time per token) rather\
    \ than asserting it without measurement."
- id: 25fcc8cd226b
  severity: writing
  text: "Address the safety regression: the manuscript highlights safety improvement\
    \ after SFT (HarmBench\u202F8.4\u202F% \u2193) but later notes a rise to 23.1\u202F\
    % after RL. Either remove the \u201Cimproves\u201D phrasing or discuss the trade\u2011\
    off explicitly."
- id: 3b8fb810f26b
  severity: science
  text: "Verify the token\u2011count statements: pre\u2011training is described as\
    \ ~10.65\u202FT tokens, yet the long\u2011context extension mentions 117\u202F\
    B tokens and the SFT tables list 47\u202FB and 167\u202FB tokens. Ensure numbers\
    \ are consistent and cited."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:36:16.903818Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript frequently extrapolates beyond the presented evidence, leading to several over‑claims. In the Introduction the authors state that Mellum 2 “achieves state‑of‑the‑art quality,” yet Table \\ref{tab:posttrain-eval-instruct} shows it is *not* the top performer on MMLU‑Pro (78.1 % vs 91.1 % for Qwen3.5‑9B). This misrepresentation is a fatal over‑reach and must be corrected.  

The performance discussion mixes latency and throughput ambiguously. Figure \\ref{fig:throughput-comparison} demonstrates a 21 % higher sustained throughput than Qwen2.5‑7B, while the text claims the model “matches … throughput” and “matches … latency.” The contradictory phrasing could mislead readers; the authors should explicitly separate latency (tokens / s) from throughput (req / s) and align the narrative with the figure.  

A central claim is that Mellum 2 “runs at the per‑token compute of a 2.5 B dense model.” No measurements (e.g., FLOPs, GPU‑time per token, or benchmarked energy) are provided to substantiate this. Without such data the claim is unsupported and constitutes an over‑reach.  

Safety reporting is inconsistent. The paper highlights an improvement after supervised fine‑tuning (HarmBench 8.4 % ↓) but later reports a degradation after RL (23.1 % ↓). The current text suggests an overall safety gain, which is inaccurate. The authors should either omit the “improves” language or discuss the trade‑off between capability gains and safety regression.  

Finally, token‑count figures are confusing. The introduction mentions a pre‑training corpus of ~10.65 T tokens, yet the long‑context extension section cites 117 B tokens, and the SFT tables list 47 B and 167 B tokens. These disparate numbers need reconciliation and proper citation; otherwise the claim of massive scale is not verifiable.  

Addressing these points will align the manuscript’s claims with the underlying data and prevent over‑statement of the model’s capabilities.
