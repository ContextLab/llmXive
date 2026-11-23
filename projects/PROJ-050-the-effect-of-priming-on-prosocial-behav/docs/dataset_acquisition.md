# Dataset Acquisition for Reddit Thread Titles

## Chosen Dataset

- **Name / Identifier**: `fddemarco/pushshift-reddit-comments`
- **Source URL**: https://huggingface.co/datasets/fddemarco/pushshift-reddit-comments
- **Access Method**: via the `datasets` Python library.

```python
from datasets import load_dataset

# Load the verified Reddit comments dataset in streaming mode.
dataset = load_dataset(
 "fddemarco/pushshift-reddit-comments",
 split="train",
 streaming=True
)
```

## Rationale

- The dataset is **verified reachable** on the project's execution environment.
- It provides a massive collection of real Reddit comments (19562139 (Wikidata Q1136, https://www.wikidata.org/wiki/Q1136) M+ records) including `author`, `body`, `created_utc`, and `subreddit`.
- It is accessed via streaming to satisfy memory constraints (< 1 GB RAM).

## Critical Data-Fit Issue (FR-001)

**Warning**: Upon acquisition and verification, it has been confirmed that the `fddemarco/pushshift-reddit-comments` dataset **does not contain the `title` field** of the parent thread.

As specified in T010 and FR-001, the priming classification requires the thread title to distinguish between "Prime" and "Control" groups. Because the only verified reachable dataset lacks this field, this constitutes a **project-blocking issue**. The pipeline will proceed with available data, but the primary hypothesis regarding priming effects cannot be tested until a title-bearing dataset is secured or the scope is revised.

## Verification Steps

1. **Check availability** – running `code/00_check_dataset.py` confirms the dataset can be streamed.
2. **Validate required fields** – verify that the following fields are present:
 - `author`
 - `body`
 - `created_utc`
 - `subreddit`

```python
# Example sanity check (executed by 00_check_dataset.py)
sample = next(iter(dataset))
assert "body" in sample, "Dataset missing 'body' field"
```
