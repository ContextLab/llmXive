# MinT Paper Storyline and Section Plan

日期：2026-05-09

## 1. 总体 Storyline

最新稿已经把 MinT 从一个工程服务提升到了 LoRA RL policy lifecycle system。下一步的主线不应推倒重写，而是把时代动机、科学贡献和系统证据扣得更紧。

最终 story 可以写成：

> AI post-training is entering a policy-population era. The second half of AI progress shifts attention from static benchmark hillclimbing to evaluation, agent-environment interaction, grounded experience, and personalization. A single foundation model will therefore support many task, branch, evaluation, tenant, and personal policies. Checkpoint-centric workflows make each policy another full-model deployment, while naive LoRA workflows lose the serving advantage by merging adapters back into full checkpoints. LoRA RL changes the state decomposition: the base model becomes a shared, slow-changing prior; the adapter becomes the mutable policy delta; rollout/routing records preserve policy computation; exported adapter revisions become immutable behavior objects; serving residency becomes transient placement below policy identity. MinT is the system abstraction that preserves this state model across rollout, update, export, evaluation, admission, eviction, and serving.

这条线的关键不是“MinT 是一个服务”，而是：

1. **Workload 变化**：post-training 从少数 checkpoints 走向大量持续演化的 policies。
2. **State 变化**：可变对象不再是 full model，而是 LoRA policy state。
3. **Boundary 变化**：训练到服务的边界从 merged/full checkpoint 变成 adapter revision。
4. **Correctness 变化**：RL policy correctness 不只由权重决定，还包括 rollout records、routing traces、backend path 和 evaluation identity。
5. **Scaling 变化**：scale-out 的关键不是 catalog lookup，而是 active diversity、warm residency 和 cold admission。

## 2. Introduction 的故事线

Introduction 需要完成六件事：

1. **时代动机**：引用 Second Half / Era of Experience，解释为什么 AI 进入 evaluation、agentic interaction、experience、personalization 阶段后，会自然产生 policy population。
2. **旧边界失效**：full fine-tuning 和 checkpoint-centric deployment 让 policy count 线性消耗 base-model memory。
3. **LoRA 的状态分解**：LoRA 让 policy update 成为小的低秩状态，但只有 service preserved policy identity 时，字节优势才会变成系统优势。
4. **RL 让问题变难**：RL 带来 optimizer state、rollout records、reward/scorer metadata、sparse routing traces 和 training-serving consistency。
5. **MinT 的系统回答**：Tinker-compatible surface + resident bases + durable policy records + exported adapter revisions + multi-LoRA serving residency。
6. **明确贡献**：用四点 scientific contributions 收束，而不是只列三项 engineering responsibilities。

建议新增/强化的 citation：

- Shunyu Yao, “The Second Half”：支持 evaluation/problem-definition 成为新阶段重点。
- Silver and Sutton, “Welcome to the Era of Experience”：支持 agents learn from experience / streams / grounded rewards / personalization。
- LoRA：继续支持低秩 adapter 表示。
- LoRA Without Regret：支持 LoRA 在 post-training/RL 中可以成为 practical substrate，而不只是 cheap approximation。
- Tinker：支持 remote post-training interface 的背景。

## 3. LoRA RL Service Problem 的故事线

这一节当前结构已经成立，应保留术语表和 lifecycle figure。

它要回答的问题是：

> Given a population of LoRA RL policies over shared resident bases, what state objects must a service preserve so that policy identity remains stable while training state, exported artifacts, routing traces, and serving residency change independently?

本节的角色：

1. 把 service problem 明确定义成 **state abstraction problem**，而不只是 RPC service problem。
2. 定义五个核心对象：base deployment、policy record、policy session、adapter revision、serving residency。
3. 解释 mutable training state 和 immutable serving/evaluation object 的区别。
4. 解释 serving addressability 和 live residency 的区别。
5. 解释 sparse routing trace 为什么是 policy computation provenance。

建议轻改：

- 第一段补一句：This is a state-abstraction problem, not merely an RPC interface problem.
- 在 sparse routing 段落里将 route consistency 明确命名为 policy computation provenance。

## 4. System Design 的故事线

System Design 要作为 state abstraction 的 realization，而不是组件清单。

章节逻辑：

1. **Control plane**：policy identity 是 durable 的；operation future 和 worker placement 是 transient 的。
2. **Trainer**：base deployment 保持 resident；mutable LoRA state 在 policy sessions 之间 restore/swap/writeback。
3. **Adapter export**：把 mutable distributed training view 转成 frozen, sampler-admissible PEFT adapter revision。
4. **Sampler**：把 exported revision 映射到 shared-base serving actor 的 local adapter id。
5. **Eviction/recovery**：eviction 改变 compute residency，不删除 policy identity。

写作原则：

- 每个组件开头都要先讲 invariant，再讲 Ray/vLLM/queue/storage 等实现。
- “Tinker-compatible” 可以出现，但不要让它主导贡献；MinT 的核心是 managed state below the programming surface。

## 5. Scale Up / Down / Out 的故事线

这一节是论文最适合承载 scientific pressure 的地方。当前稿已经比较强，建议只做术语强化。

### 5.1 Scale Up

要证明大 dense/MoE base 让 base residency 和 computation provenance 成为必要。

核心 claim：

- large base deployment is too expensive to reload per policy；
- distributed LoRA state must be restored per policy；
- sparse/MoE rollout path is part of policy computation；
- routing traces scale with tokens, not with base parameters。

### 5.2 Scale Down

要证明 adapter revision 是 training-serving boundary。

核心 claim：

- full checkpoint handoff scales with base size；
- merge-based LoRA loses serving advantage；
- exported PEFT adapter revision preserves behavior while excluding base bytes；
- evaluation object includes adapter revision, base compatibility, target modules, prompt renderer, scorer, and serving path。

### 5.3 Scale Out

要证明 policy population serving 是 residency problem。

核心 claim：

- catalog size is namespace scale；
- active diversity is execution scale；
- host warm cache and GPU-active window are bounded；
- cold admission must be explicit, deduplicated, and backpressured。

建议补一句：

> Catalog size determines how many policies are addressable; active diversity and cold-admission rate determine the execution scale.

## 6. Evaluation 的故事线

Evaluation 不一定要重排，但建议在开头加一张 claim-to-evidence map。

| Scientific claim | Evidence | Role |
| --- | --- | --- |
| Adapter revision can replace full checkpoint handoff | 4B/30B handoff vs merge | training-serving boundary |
| Mutable policy state can survive worker/session changes | resume / concurrent training pilots | lifecycle correctness |
| Sparse RL needs computation provenance | Qwen3/GLM routing traces and masking | policy correctness |
| LoRA RL can reach large sparse bases | Qwen3-235B and Kimi K2 deployment record | scale-up evidence |
| Scale-out is bounded by residency, not namespace lookup | 30B multi-LoRA serving, 100k catalog | residency envelope |
| Representation affects cold admission | packed MoE LoRA loader | future optimization direction |

写作注意：

- 不 claim 打败 S-LoRA/Punica/dLoRA/vLLM。
- Kimi K2 保持 operational deployment record，不写成 matched reproducible benchmark。
- concurrent training 保持 pilot，不写成 scheduler law。
- 100k / 1M / 10^7 的边界要清楚。

## 7. Related Work 的故事线

Related Work 当前分组合理，建议补强每组的 “what they abstract vs what MinT abstracts”。

### 7.1 Service interfaces

Tinker / OpenTinker / SkyRL tx 解决的是 remote post-training programming surface。

MinT 的定位：

> Tinker answers how users program remote post-training; MinT asks what state a LoRA RL service must preserve so that a trained adapter remains the same policy across rollout, update, export, evaluation, and serving.

### 7.2 RL execution systems

HybridFlow / AReaL / OpenRLHF / Relax / ROLL 解决 rollout/training placement、dataflow、asynchrony、staleness、cost。

MinT 的定位：

> These systems optimize execution of post-training loops; MinT defines the policy-state boundary that survives across execution, export, and serving.

### 7.3 Multi-LoRA serving

Punica / S-LoRA / dLoRA / vLLM 解决 already-produced adapters 的 batching、memory、kernel、scheduling。

MinT 的定位：

> Multi-LoRA serving systems optimize the serving substrate; MinT connects that substrate to the upstream RL lifecycle that creates adapter revisions with identity, provenance, and evaluation records.

### 7.4 Large-model infrastructure

Ray / HybridFlow / DeepSeek-V4 说明 modern infrastructure 的关键是识别 state unit 和 resource accounting。

MinT 的定位：

> MinT applies this resource-accounting view to LoRA policy state: adapter tensors, optimizer state, routing traces, resident cache tiers, and GPU-active adapter slots.

## 8. Conclusion 的故事线

Conclusion 需要回到同一个大 story，而不只是总结实验。

推荐顺序：

1. LoRA RL turns post-training behavior into small but stateful policy objects.
2. MinT preserves those objects across rollout, update, export, serving admission, eviction, and later selection.
3. Experiments show the abstraction scales down handoff, scales up to sparse/MoE bases, and scales out through residency tiers.
4. Future policy populations will need better representation, consistency, placement, governance, and population-level learning.

## 9. 本轮正文修改清单

P0:

1. Introduction 开头加入 policy population motivation paragraph。
2. Introduction 结尾加入 four contributions paragraph。
3. Related Work service-interface 段强化 Tinker vs MinT 区分。
4. `paper.bib` 增加真实可核验条目：Second Half、Era of Experience、LoRA Without Regret。

P1:

1. Problem section 补 state-abstraction framing。
2. Scale Up / Scale Out 补 provenance 和 execution-scale 术语。
3. Evaluation 开头加 claim-to-evidence map。
4. Conclusion 补 policy-population era 的收束。

P2:

1. 删除 `% DELEGATE` 内部注释。
2. 删除未使用的 `\placeholder`。
3. 修正文中明显 typo：`from a   number`。
4. 编译并检查 missing citations / undefined refs / overfull boxes。
