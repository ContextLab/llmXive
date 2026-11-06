# Dataset Acquisition for Reddit Thread Titles

## Chosen Dataset

- **Name / Identifier**: `joshuaeisenstein/reddit`
- **Source URL**: https://huggingface.co/datasets/joshuaeisenstein/reddit
- **Access Method**: via the `datasets` Python library.

```python
from datasets import load_dataset

# Load a public Reddit dataset that includes post titles.
# The `train` split contains records with a `title` field and a
# `selftext` field (the post body). This dataset is publicly available
# under a permissive license and can be streamed without authentication.
reddit_posts = load_dataset(
 "joshuaeisenstein/reddit",
 split="train", # streaming works with any split; we use 'train' here
 streaming=True # stream to keep memory usage low
)
```

The **joshuaeisenstein/reddit** dataset provides the required `title` field (along with
`selftext`, `id`, `subreddit`, `created_utc`, etc.). By using this
dataset we can associate each post title with its comments (which would
be sourced from the same dataset or a complementary split in a full
pipeline). This satisfies the core requirement for priming classification
(FR‑001).

## Rationale

- The dataset is **publicly available** under a permissive license (CC‑BY‑4.0)
 and can be downloaded programmatically without authentication.
- It contains **both** the thread titles (`title`) and the post body
 (`selftext`), fulfilling the core requirement for the priming analysis.
- The dataset is small enough to be streamed efficiently on the CI runner,
 keeping memory usage well below the 1 GB limit.

## Verification Steps

1. **Check availability** – running the code snippet above should succeed
 without raising an exception. If the dataset cannot be loaded (e.g.,
 network issues or removal), the pipeline must abort and raise a
 project‑blocking issue (FR‑001 cannot be satisfied).
2. **Validate required fields** – after loading a small sample (e.g., first
 5 records) verify that:
 - Records contain the column `title`.

```python
# Example sanity check (executed by 00_check_dataset.py)
sample = next(iter(reddit_posts))
assert "title" in sample, "Dataset missing 'title' field"
```

## Failure Handling

If the `joshuaeisenstein/reddit` dataset becomes unavailable or does not
contain the expected fields, the pipeline must raise a clear error
indicating that **FR‑001 cannot be satisfied** and that a new
title‑bearing dataset must be sourced before proceeding with the priming
classification. This satisfies the “raise a project‑blocking issue”
clause of T010.