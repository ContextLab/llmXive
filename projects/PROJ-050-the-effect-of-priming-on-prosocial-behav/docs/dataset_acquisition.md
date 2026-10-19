# Dataset Acquisition for Reddit Thread Titles

## Chosen Dataset

- **Name / Identifier**: `pushshift.io/reddit`
- **Source URL**: https://huggingface.co/datasets/pushshift.io/reddit
- **Access Method**: via the `datasets` Python library.

 ```python
 from datasets import load_dataset

 # Submissions (contain thread titles)
 submissions = load_dataset(
 "pushshift.io/reddit",
 split="submissions", # each record has a `title` field
 streaming=True # stream to keep memory usage low
)

 # Comments (contain the reply bodies)
 comments = load_dataset(
 "pushshift.io/reddit",
 split="comments",
 streaming=True
)
 ```

The **submissions** split provides the required `title` field (along with `subreddit`, `id`, `created_utc`, etc.).
The **comments** split provides the comment text (`body`), author information, timestamps, and a `link_id` that references the parent submission (`t3_<submission_id>`).
By joining `comments.link_id` (after stripping the `t3_` prefix) with `submissions.id`, we can associate each comment with its thread title, enabling the priming classification required by FR‑001.

## Rationale

- The dataset is **publicly available** under a permissive license (CC‑BY‑4.0) and can be downloaded programmatically without authentication.
- It contains **both** the thread titles (in the submissions split) **and** the comment bodies (in the comments split), fulfilling the core requirement for the priming analysis.
- {{claim:c_82ac8aa7}} (Wikidata Q108943604, https://www.wikidata.org/wiki/Q108943604)

## Verification Steps

1. **Check availability** – running the code snippet above should succeed without raising an exception. If the dataset cannot be loaded (e.g., network issues or removal), the pipeline must abort and raise a project‑blocking issue (FR‑001 cannot be satisfied).
2. **Validate required fields** – after loading a small sample (e.g., first 10 records) verify that:
 - Submissions contain the column `title`.
 - Comments contain the column `link_id` that can be linked to a submission `id`.

```python
# Example sanity check (not part of the final pipeline)
sample_sub = next(iter(submissions))
assert "title" in sample_sub, "Submissions missing 'title' field"

sample_com = next(iter(comments))
assert "link_id" in sample_com, "Comments missing 'link_id' field"
```

## Failure Handling

If the `pushshift.io/reddit` dataset becomes unavailable or does not contain the expected fields, the pipeline must raise a clear error indicating that **FR‑001 cannot be satisfied** and that a new title‑bearing dataset must be sourced before proceeding with the priming classification. This satisfies the “raise a project‑blocking issue” clause of T010.