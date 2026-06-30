# Reproduce & validate: ProRL: Effective Reinforcement Learning for Proactive Recommendation via Rectified Policy Gradient Estimation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/   (clone of https://github.com/hongruhou89/ProRL)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** ProRL: Effective Reinforcement Learning for Proactive Recommendation via Rectified Policy Gradient Estimation

**Abstract:** Proactive Recommender Systems (PRSs) aim to guide user preference shift toward target items by generating paths of intermediate recommendations. Reinforcement learning (RL) provides a principled framework for optimizing such sequential decision tasks, as path rewards can naturally capture both short-term acceptance and long-term guidance effectiveness. However, naively applying policy gradients to PRS results in deficient gradient estimation. We identify two deficiencies: (1) path-level rewards decompose into step-level rewards with positive mean, creating a length-dependent bias that causes gradients to favor path extension over meaningful exploration; (2) weighting each step by the entire path-level reward ignores the decomposition structure, leading to high gradient variance. To rectify these two deficiencies, we propose an effective RL framework ProRL with two novel mechanisms for proactive recommendation. First, Stepwise Reward Centering subtracts expected rewards to neutralize length-dependent bias, ensuring that path extension yields zero expected gradient signal. Second, Position-Specific Advantage Estimation leverages the reward decomposition structure to compute step-dependent baselines, reducing gradient variance. Together, these mechanisms yield policy gradients that precisely target path quality. Our experiments on three real-world datasets demonstrate that ProRL significantly outperforms state-of-the-art PRSs. Our code is available at https://github.com/hongruhou89/ProRL.

## Shipped code — file tree (`projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/`)

```
Proactive_RL_prorl.py
README.md
ckpt/Books/Oct-21-2025_15-59-81c0bc/Oct-21-2025_15-59-81c0bc.pth
ckpt/GRU4Rec-amazon-books.pth
ckpt/GRU4Rec-ml-1m-sas.pth
ckpt/GRU4Rec-steam-merged.pth
ckpt/SASRec-amazon-books.pth
ckpt/SASRec-ml-1m-sas.pth
ckpt/SASRec-steam-merged.pth
ckpt/Steam/Oct-10-2025_13-18-0b6ea4/Oct-10-2025_13-18-0b6ea4.pth
ckpt/ml-1m/Aug-20-2025_23-29-662bab/Aug-20-2025_23-29-662bab.pth
collator.py
config/amazon-books_gru4rec_config.yaml
config/amazon-books_sasrec_config.yaml
config/ml-1m-sas_gru4rec_config.yaml
config/ml-1m-sas_sasrec_config.yaml
config/prorl.yaml
config/ptconfig.yaml
config/rec_config.yaml
config/steam-merged_gru4rec_config.yaml
config/steam-merged_sasrec_config.yaml
data_utils.py
dataset.py
datasets/Books/Books.datamaps
datasets/Books/Books.test
datasets/Books/Books.train
datasets/Books/Books.val
datasets/Books/qwen3-embedding-8b-pca.sem_ids
datasets/Steam/Steam.datamaps
datasets/Steam/Steam.test
datasets/Steam/Steam.train
datasets/Steam/Steam.val
datasets/Steam/qwen3-embedding-8b-pca.sem_ids
datasets/amazon-books/amazon-books.inter
datasets/amazon-books/amazon-books.item
datasets/ml-1m/ml-1m.datamaps
datasets/ml-1m/ml-1m.test
datasets/ml-1m/ml-1m.train
datasets/ml-1m/ml-1m.val
datasets/ml-1m/qwen3-embedding-8b-pca.sem_ids
datasets/ml-1m-sas/ml-1m-sas.inter
datasets/ml-1m-sas/ml-1m-sas.item
datasets/ml-1m-sas/ml-1m-sas.user
datasets/steam-merged/steam-merged.inter
datasets/steam-merged/steam-merged.item
evaluator.py
fig/framework.png
model.py
proactive_pretrain.py
scripts/Pretrain/run_books_pretrain.sh
scripts/Pretrain/run_ml1m_pretrain.sh
scripts/Pretrain/run_steam_pretrain.sh
scripts/RL/run_books_prorl.sh
scripts/RL/run_ml1m_prorl.sh
scripts/RL/run_steam_prorl.sh
scripts/run_pretrain.sh
scripts/run_prorl.sh
tokenizer.py
trainer.py
trainer_RL_prorl.py
utils.py
```

## Detected entry points

- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/Proactive_RL_prorl.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/collator.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/data_utils.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/dataset.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/evaluator.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/model.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/proactive_pretrain.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/tokenizer.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/trainer.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/trainer_RL_prorl.py`
- `projects/PROJ-640-https-arxiv-org-abs-2605-28293/external/ProRL/utils.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `ProRL` — not re-implementing it.
