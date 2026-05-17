---
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:51:43.817132Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript presents a robust system design but contains specific instances where the Abstract and Introduction extrapolate beyond the explicit evidence provided in the Evaluation section, constituting over-claiming.

First, the Abstract claims "adapter-only handoff reduces the measured handoff step by $18.3\times$ on a 4B dense model and by $2.85\times$ on a 30B MoE model" (Abstract, lines 14–15). However, Table 1 (Section 5.2, lines 566–580) reports "Cold first sample" latencies for the same models. For the 4B model, the ratio is $55.704 / 4.114 \approx 13.5\times$, not $18.3\times$. For the 30B MoE model, the ratio is $156.074 / 117.304 \approx 1.33\times$, significantly lower than the claimed $2.85\times$. While "materialization" times differ vastly, the Abstract does not clarify that these specific speedup figures exclude the cold-sample generation time or refer to a different metric. Presenting higher aggregate speedups in the Abstract without clear definition in the context of the main evaluation table overstates the measured benefit relative to the provided data.

Second, regarding the "million-scale" policy catalog, the Abstract states "Experimental validation demonstrates the infrastructure's ability to manage million-scale LoRA policy catalogs" (Abstract, lines 38–39). Section 5.1 (lines 320–325) and Section 6 (lines 530–535) clarify that the main experiments sweep catalogs up to 100K entries, while the $10^6$ figure is an extrapolation derived from Appendix Table A6 ("fleet_model", lines 900–915). While the distinction between "addressability" and "residency" is noted in the body, the Abstract's use of "Experimental validation demonstrates" implies direct measurement of the million-scale capability. This conflates measured bounds with modeled capacity, which is a form of scope overreach.

To address these overclaims, please align the Abstract's performance figures with the specific metrics in Table 1 or explicitly define the "handoff step" metric used for the $18.3\times$/$2.85\times$ figures. Additionally, soften the Abstract's claim on million-scale management to reflect that this is a modeled capacity based on 100K measurements, rather than direct experimental validation of the full scale. These adjustments are necessary to ensure the summary claims do not exceed the evidence boundary established in the Evaluation section.
