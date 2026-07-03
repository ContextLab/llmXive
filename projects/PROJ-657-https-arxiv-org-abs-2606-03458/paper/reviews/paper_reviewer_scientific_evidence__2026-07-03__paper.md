---
action_items:
- id: 360fd4285f96
  severity: science
  text: "The claim that KVarN achieves SOTA on AIME24 and MATH500 relies on a single\
    \ run (or unspecified n) for the proposed method, while baselines like KIVI report\
    \ standard deviations (e.g., 60.0\xB11.1 vs 55.5\xB16.9 in Tab 1). To validate\
    \ statistical significance, the authors must report the number of independent\
    \ seeds (n) for KVarN and perform a t-test or report confidence intervals for\
    \ the proposed method's gains."
- id: f6bb85d4ca8c
  severity: science
  text: The 'pseudo-decode' evaluation method (Sec 3.2, Fig 4) is a novel proxy for
    error accumulation but lacks validation against true autoregressive decoding.
    The authors should demonstrate a strong correlation between the pseudo-decode
    error metrics and actual end-to-end reasoning performance on a held-out subset
    to prove the proxy's predictive validity.
- id: fa6675b8948f
  severity: science
  text: The paper claims KVarN outperforms eviction methods (SnapKV, PyramidKV) at
    equivalent memory footprint (Tab 5, Appendix). However, the comparison mixes quantization
    (2-bit) with eviction (7x compression of 16-bit). The authors must clarify if
    the 'equivalent footprint' claim holds strictly for the KV-cache size or if it
    includes the overhead of storing eviction indices, and ensure the comparison is
    fair regarding total memory usage.
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:19:15.636333Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented for KVarN is generally robust in its experimental design, utilizing multiple models (Qwen3-4B, Llama-3.1-8B, Phi-4-14B) and diverse benchmarks (reasoning, code, instruction following, retrieval). The decomposition of error into magnitude and directional components (Eq. 2, Fig 1) provides a compelling mechanistic explanation for the observed improvements, supported by the visual evidence in Figure 1b showing reduced token norm deviation.

However, the statistical rigor regarding the primary claims of "substantial improvement" requires strengthening. In Table 1 (AIME24/MATH500), the proposed method's results are presented as point estimates (e.g., 60.0%) or with standard deviations that appear to be derived from a single run or a very small sample size, whereas baselines like KIVI show larger variances (e.g., 55.5±6.9). Without reporting the number of independent seeds (n) for KVarN and conducting a statistical significance test (e.g., paired t-test) against the baselines, the claim of "substantial improvement" is not fully supported by the evidence. The observed gains, while positive, could potentially be within the noise floor of the evaluation metric, especially given the high variance in reasoning tasks.

Furthermore, the "pseudo-decode" evaluation method introduced in Section 3.2 is a critical contribution for efficiently measuring error accumulation. While the results in Figure 4 suggest KVarN accumulates less error than KIVI, the paper does not explicitly validate this proxy against full autoregressive decoding. A correlation analysis between the pseudo-decode error metrics and the actual end-to-end accuracy on a held-out set of reasoning problems is necessary to confirm that the proxy accurately predicts real-world performance degradation.

Finally, the comparison with eviction-based methods in the Appendix (Table 5) requires clarification on the definition of "equivalent memory footprint." The authors compare 2-bit quantization against 7x compressed 16-bit eviction methods. While the bit-widths may align, the overhead of storing eviction indices or the specific implementation details of the 7x compression (e.g., does it include the prompt cache?) must be explicitly detailed to ensure the comparison is fair and the claim of superiority is scientifically sound. The current presentation risks conflating quantization efficiency with eviction efficiency without a unified cost model.
