---
action_items: []
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:35:57.369657Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.5
verdict: accept
---

The manuscript presents a thorough empirical investigation of KV‑Cache quantization error accumulation during long‑horizon decoding and proposes the KVarN method to mitigate this effect. From a scientific‑evidence standpoint, the paper demonstrates a high level of rigor:

1. **Experimental Design & Controls** – The authors evaluate KVarN against a comprehensive set of baselines (KIVI, QuaRot, KVQuant‑1 %, PolarQuant, TurboQuant, Kitty) across three distinct model families (Qwen3‑4B, Llama‑3.1‑8B, Phi‑4‑14B). This breadth of comparison (see Tables \ref{tab:math_reasoning_results}, \ref{tab:humaneval_results}, \ref{tab:ifeval_results_horizontal}, \ref{tab:kv_quant_results}) serves as an effective control for confounding factors such as model architecture, token length, and precision allocation.

2. **Sample Sizes & Replication** – For the reasoning benchmarks (MATH500, AIME24) the authors report results over the full benchmark (500 and 30 items respectively) and repeat each experiment three times, providing mean ± std. HumanEval is evaluated on its standard 164‑problem set, again with three runs. The line‑retrieval task uses 100 random queries per context length, and the pseudo‑decode proxy is evaluated over multiple block sizes. These sample sizes are sufficient to detect the reported effect sizes (e.g., a 4.5 % absolute gain on AIME24 over KIVI, Table \ref{tab:math_reasoning_results}).

3. **Effect Size & Statistical Significance** – Improvements are consistent across all metrics: KVarN reduces token‑scale magnitude error (Fig. \ref{fig:scale:b}), lowers accumulated attention‑output MAE (Fig. \ref{fig:output_mae_vs_rtn}), and yields higher end‑to‑end accuracy on all downstream tasks (e.g., 88.4 % ± 0.3 on HumanEval vs. 86.4 % ± 1.3 for KIVI, Table \ref{tab:humaneval_results}). The magnitude of these gains, while modest, is statistically meaningful given the low variance across runs.

4. **Risk of P‑hacking / Over‑fitting** – The authors pre‑register a clear hypothesis (token‑scale errors dominate accumulation) and provide an a‑priori decomposition (Eq. \ref{eq:decompose}) that guides method design. They also include ablation studies (Hadamard‑only, VarN‑only) in Fig. \ref{fig:token-norm} and the appendix (Fig. \ref{fig:joint}), demonstrating that the reported gains are not the result of selective reporting.

5. **Robustness Checks** – The pseudo‑decode evaluation (Sec. \ref{sec:err_acc}, Fig. \ref{fig:pseudo-decode}) directly simulates the error‑accumulation regime, and the authors verify that KVarN’s advantage grows with context length (Fig. \ref{fig:output_mae_vs_rtn}). Moreover, runtime overhead is quantified (Fig. \ref{fig:timing}) and shown to be negligible (<0.2 %).

6. **Alternative Explanations** – The authors discuss why incoherence processing alone is insufficient (Sec. \ref{sec:rotate}) and why dual‑scaling specifically addresses token‑scale drift, supporting the causal claim that variance‑normalization is the key driver of the observed improvements.

Overall, the empirical evidence is strong, well‑controlled, and reproducible (code and algorithm details are provided, e.g., Alg. \ref{alg:sinq}). No major methodological flaws or unsupported statistical claims are identified. Consequently, the paper meets the standards for acceptance based on the strength of its scientific evidence.
