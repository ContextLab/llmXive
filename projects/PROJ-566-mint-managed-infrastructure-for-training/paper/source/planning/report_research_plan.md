# MinT Technical Report Workbench Plan

Date: 2026-05-01

MinT should be written as a systems report about LoRA RL as a service. The service trains many LoRA policies over shared base models, transfers adapters from training to inference without moving full models, and serves large policy catalogs with bounded active memory. Tinker compatibility is the user-programming surface; the systems content is the training, adapter-transfer, and serving machinery behind that surface.

## Paper Spine

The report should follow the structure used by strong systems papers rather than a product manual.

- Ray starts from a coupled RL workload, derives requirements, then introduces the system abstraction and evaluates those requirements.
- HybridFlow/verl starts from RLHF dataflow, model placement, transfer, and training/generation resharding, then measures throughput and resource use under controlled placements.
- DeepSeek-V4 names concrete infrastructure state: cache entries, cache tiers, persistent rollout state, teacher state, and recomputation tradeoffs.

For MinT, the corresponding state is: base model, LoRA adapter, optimizer state, sparse-route metadata, exported sampler weights, serving alias, adapter catalog, resident adapter tier, and GPU-active adapter slots.

## Claims

1. LoRA RL lets users create many task, tenant, branch, or personal policies over a small number of expensive base models.
2. MinT keeps the LoRA policy usable across training, evaluation, transfer, and serving.
3. MinT scales up to large dense/MoE models, scales down by transferring adapters rather than full model copies or merged weights, and scales out to large adapter catalogs with cache tiers.
4. The open slice, `verl-mint` plus `mint-cookbook`, should reproduce public small/medium results. Larger model evidence can appear as closed deployment evidence, with release boundaries stated plainly.

## Writing Delegation

The paper body should not render owner names. The source uses `DELEGATE` comments where a section needs a named owner, and this plan is the explicit assignment list.

| Section or evidence block | Owner | Output expected |
|---|---|---|
| Introduction and final synthesis | Yiwen, with Lucian for user-facing motivation | Rewrite only around the real MinT thesis: LoRA RL as many-policy service over shared base models. No product pitch language. |
| Tinker-compatible surface and `verl-mint` | Nolan | Verify the public contract, the open-source boundary, and what can be claimed from `verl-mint` without closed infrastructure. |
| Cookbook benchmark suite | Leixiang | Provide compact result rows for DAPO-AIME24, FinGPT, LawBench, and chat-DPO, including task metric, model, rank, runtime/GPU budget, and artifact envelope. |
| Multi-LoRA serving and `10^7` catalog scale | Changhai | Provide the trained-adapter serving result and the stress result separately: active adapters, resident adapters, catalog size, cache hit rate, latency, throughput, error rate, and score delta. |
| Large sparse and MoE runs | Songlin, with Yiwen for GLM-5.1 if used | Provide Qwen3-30B route-consistency rows, Qwen3-235B rows, GLM-5.1 rows, and task metrics where available. Mark support-only runs as operational validation, not result rows. |
| Time-sliced multi-LoRA training | Nolan | Compare dedicated-trainer and time-sliced schedules with fixed data order, optimizer, rank, slice length, and update budget. |
| Adapter transfer speed | Nolan, with Yiwen for comparison language | Measure adapter export/load/first-token path against merge/full-copy movement when a real baseline exists; keep static LoRA kernel overhead out of the main claim. |
| Related-work positioning | Yiwen, with Nolan checking SkyRL tx/OpenTinker details | Keep direct comparisons to matched model/task/budget/metric settings; otherwise use related work for positioning only. |

## Experiment Breakdown

| ID | Claim | Owner | System and model | Task | Metrics | Expected result |
|---|---|---|---|---|---|---|
| E1 Speed: adapter transfer versus merge | MinT can move a trained LoRA policy from trainer to inference faster than merged/full-model movement. | Nolan, Yiwen | MinT trainer plus MinT serving path. Primary: `Qwen/Qwen3-4B-Instruct-2507`. Extension: `Qwen/Qwen3-30B-A3B-Instruct-2507`. | Use a trained DAPO-AIME24 adapter and a fixed eval prompt set. Compare adapter export/load/first-token path with a merge-and-serve path when available. | export time, transfer bytes, load/admission time, time to first token, p50/p95 serving latency, throughput, eval metric agreement against isolated adapter serving. | Adapter transfer should dominate merge/full-copy movement on latency and bytes while preserving the adapter's eval score. |
| E2 Memory: multi-LoRA versus single-adapter serving under the same budget | MinT serves more trained policies for one base model by sharing frozen weights and bounding active adapter memory. | Changhai | MinT integrated multi-LoRA serving. Primary: `Qwen/Qwen3-4B-Instruct-2507`; MoE extension if enough adapters exist. | Uniform and Zipf request streams over trained cookbook adapters. Synthetic adapters only for stress extension. | trained adapters served, resident adapters, GPU-active adapters, HBM slope, CPU memory slope, p50/p95 latency, throughput, error rate, score delta versus isolated serving. | Multi-LoRA should increase selectable trained policies under fixed memory while keeping GPU-active slots bounded and score delta near zero. |
| E3 Public cookbook suite | MinT produces real task improvement across more than one narrow math RL path. | Leixiang | MinT plus `mint-cookbook` on `Qwen/Qwen3-4B-Instruct-2507`. | Report the meaningful maintained lines without stuffing the paper: DAPO-AIME24 for math RL, FinGPT Fineval and sentiment for finance SFT, LawBench for legal-domain scoring, chat-DPO for pairwise preference training. | base metric, trained metric, reward/eval curve where applicable, pass@k where applicable, samples or examples, optimizer steps, GPU hours, hardware, artifact envelope. | Public rows should show a reproducible benchmark lift or a clearly marked runnable benchmark contract. The paper should present a compact suite table plus selected deeper rows, not a catalog of every command. |
| E4 Best practice: reproducible open workflow | The open slice gives users a working MinT-style training path rather than a private-only claim. | Nolan, Leixiang | `verl-mint` and `mint-cookbook`. Primary: `Qwen/Qwen3-0.6B` and selected `Qwen/Qwen3-4B-Instruct-2507` cookbook lines. | `verl-mint` smoke plus the selected cookbook suite rows. | exact command, model, dataset snapshot, final metric, runtime, GPU type/count, failure count across repeated runs, artifact envelope. Repository hashes belong in run logs or supplementary bundles, not in the paper text. | A reader should be able to run the public workflow and obtain the reported metric envelope without closed infrastructure. |
| E5 Scale out: `10^7` addressable LoRA policies | MinT can name and select from a catalog much larger than the GPU-active adapter set. | Changhai | MinT serving catalog/cache stack over one base model. Use trained adapters for quality-bearing rows and synthetic catalog entries for scale rows. | Alias-scale workload over `10^7` policy records; adapter-scale workload over the largest feasible distinct adapter set. | addressable policy count, distinct adapter revisions, lookup latency, admission latency, cache hit rate, p50/p95 latency, throughput, success rate, eviction rate. | Lookup and admission should remain stable at catalog scale; latency should follow cache-hit and active-slot pressure rather than catalog cardinality alone. |

## Secondary Required Experiment

Time-sliced multi-LoRA training is a support claim for the service model, but it should not displace the serving-scale experiments.

- Owner: Nolan.
- System and model: MinT time-sliced training on `Qwen/Qwen3-4B-Instruct-2507`; larger-model row only if a clean run exists.
- Task: train multiple DAPO-AIME24 adapters from the same base with fixed seeds or deterministic data shards.
- Metrics: number of policies, trainer replicas, slice length, switch time, save/load time, GPU-hours per adapter, adapters per trainer-hour, learning-curve deviation against dedicated trainers, final score distribution.
- Expected result: time slicing should reduce base-model replica demand while keeping optimizer histories isolated and final scores close to dedicated training.

## Related-Work Positioning

- SkyRL tx is the closest direct Tinker-compatible backend peer. Use a matched run only when the same model, task, budget, and metric can be held fixed.
- OpenTinker is RL-as-a-Service context and must be discussed. Do not treat it as a direct baseline unless a matched protocol is runnable.
- AReaL, HybridFlow/verl, Relax, ROLL, and OpenRLHF define the RL execution comparison space: throughput, placement, task quality, and resource use.
- Punica, S-LoRA, dLoRA, and vLLM define the multi-LoRA serving substrate. vLLM is an implementation dependency inside MinT, not a baseline "against" MinT.

## Cut List

Do not present these as main paper experiments:

- API pass/fail matrices.
- Feature compatibility tables.
- Adapter publication time.
- Cold-first-touch debugging logs.
- Standalone LoRA-enabled versus base-inference overhead.
- vLLM multi-LoRA as a baseline against MinT.
- Page counts or paper-length comparisons.
