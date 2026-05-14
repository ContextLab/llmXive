# Reference Markdown Manifest

This directory stores Markdown captures of the reference papers listed by the user.

Default arXiv capture pattern: `https://markdown.new/https://arxiv.org/html/<arxiv_id>`.
When arXiv HTML was unavailable or unstable, the file front matter records the actual fallback source or saved notice.

| File | Direction | Title | arXiv ID | Core | Source | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `01-2309.06180-efficient-memory-management-for-large-language-model-serving-with-pageda.md` | Serving | Efficient Memory Management for Large Language Model Serving with PagedAttention | 2309.06180 | no | https://arxiv.org/html/2309.06180 | no arxiv html saved notice |
| `02-no-arxiv-orca-a-distributed-serving-system-for-transformer-based-generative-model.md` | Serving | Orca: A Distributed Serving System for Transformer-Based Generative Models | none | no | https://www.usenix.org/conference/osdi22/presentation/yu | ok |
| `03-2401.09670-distserve-disaggregating-prefill-and-decoding-for-goodput-optimized-larg.md` | Serving | DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving | 2401.09670 | no | https://arxiv.org/html/2401.09670 | ok |
| `04-2409.19256-hybridflow-a-flexible-and-efficient-rlhf-framework.md` | RLHF System | HybridFlow: A Flexible and Efficient RLHF Framework | 2409.19256 | yes | https://arxiv.org/html/2409.19256 | ok |
| `05-1909.08053-megatron-lm-training-multi-billion-parameter-language-models-using-model.md` | Scale-up | Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism | 1909.08053 | no | https://arxiv.org/html/1909.08053 | no arxiv html saved notice |
| `06-2104.04473-efficient-large-scale-language-model-training-on-gpu-clusters-using-mega.md` | Scale-up | Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM | 2104.04473 | no | https://arxiv.org/html/2104.04473 | no arxiv html saved notice |
| `07-1910.02054-zero-memory-optimizations-toward-training-trillion-parameter-models.md` | Scale-up | ZeRO: Memory Optimizations Toward Training Trillion Parameter Models | 1910.02054 | no | https://arxiv.org/html/1910.02054 | no arxiv html saved notice |
| `08-2504.14960-moe-parallel-folding-heterogeneous-parallelism-mappings-for-efficient-la.md` | Scale-up MoE | MoE Parallel Folding: Heterogeneous Parallelism Mappings for Efficient Large-Scale MoE Model Training with Megatron Core | 2504.14960 | yes | https://arxiv.org/html/2504.14960 | ok |
| `09-2601.14243-jet-rl-enabling-on-policy-fp8-reinforcement-learning-with-unified-traini.md` | RL Consistency | Jet-RL: Enabling On-Policy FP8 Reinforcement Learning with Unified Training and Rollout Precision Flow | 2601.14243 | yes | https://arxiv.org/html/2601.14243 | ok |
| `10-no-arxiv-on-the-rollout-training-mismatch-in-modern-rl-systems.md` | RL Consistency | On the Rollout-Training Mismatch in Modern RL Systems | none | no | https://openreview.net/pdf/325f91538e61ba160793adc5029888c00d06fa7a.pdf | ok |
| `11-2510.11370-stabilizing-moe-reinforcement-learning-by-aligning-training-and-inferenc.md` | RL Consistency MoE | Stabilizing MoE Reinforcement Learning by Aligning Training and Inference Routers | 2510.11370 | yes | https://arxiv.org/html/2510.11370 | ok |
| `12-2505.24298-areal-a-large-scale-asynchronous-reinforcement-learning-system-for-langu.md` | Async RL System | AReaL: A Large-Scale Asynchronous Reinforcement Learning System for Language Reasoning | 2505.24298 | no | https://arxiv.org/html/2505.24298 | ok |
| `13-2510.12633-laminar-a-scalable-asynchronous-rl-post-training-framework.md` | Async RL System | Laminar: A Scalable Asynchronous RL Post-Training Framework | 2510.12633 | no | https://arxiv.org/html/2510.12633 | ok |
| `14-2106.09685-lora-low-rank-adaptation-of-large-language-models.md` | LoRA | LoRA: Low-Rank Adaptation of Large Language Models | 2106.09685 | no | https://arxiv.org/html/2106.09685 | ok |
| `15-2303.10512-adalora-adaptive-budget-allocation-for-parameter-efficient-fine-tuning.md` | LoRA Compression | AdaLoRA: Adaptive Budget Allocation for Parameter-Efficient Fine-Tuning | 2303.10512 | no | https://arxiv.org/html/2303.10512 | ok |
| `16-2305.14314-qlora-efficient-finetuning-of-quantized-llms.md` | LoRA Quantization | QLoRA: Efficient Finetuning of Quantized LLMs | 2305.14314 | no | https://arxiv.org/html/2305.14314 | no arxiv html saved notice |
| `17-2407.00066-compress-then-serve-serving-thousands-of-lora-adapters-with-little-overh.md` | LoRA Compression Serving | Compress then Serve: Serving Thousands of LoRA Adapters with Little Overhead | 2407.00066 | yes | https://ar5iv.labs.arxiv.org/html/2407.00066 | ok via ar5iv fallback |
| `18-2310.18547-punica-multi-tenant-lora-serving.md` | Multi-LoRA Serving | Punica: Multi-Tenant LoRA Serving | 2310.18547 | yes | https://arxiv.org/html/2310.18547 | no arxiv html saved notice |
| `19-2311.03285-s-lora-serving-thousands-of-concurrent-lora-adapters.md` | Multi-LoRA Serving | S-LoRA: Serving Thousands of Concurrent LoRA Adapters | 2311.03285 | yes | https://arxiv.org/html/2311.03285 | ok |
| `20-2505.03756-improving-the-serving-performance-of-multi-lora-large-language-models-vi.md` | Multi-LoRA Cache | Improving the Serving Performance of Multi-LoRA Large Language Models via Efficient LoRA and KV Cache Management / FASTLIBRA | 2505.03756 | yes | https://arxiv.org/html/2505.03756 | ok |
| `21-2511.22880-serving-heterogeneous-lora-adapters-in-distributed-llm-inference-systems.md` | Heterogeneous LoRA Serving | Serving Heterogeneous LoRA Adapters in Distributed LLM Inference Systems / LoRAServe | 2511.22880 | yes | https://arxiv.org/html/2511.22880 | ok |

## Core References Noted By User

2409.19256, 2504.14960, 2601.14243, 2510.11370, 2407.00066, 2310.18547, 2311.03285, 2505.03756, 2511.22880
