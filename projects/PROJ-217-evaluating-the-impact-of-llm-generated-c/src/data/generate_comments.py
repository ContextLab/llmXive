import json
import os
import time
from pathlib import Path
from typing import List, Dict

import tiktoken
from huggingface_hub import InferenceClient
# In newer versions of huggingface_hub the InferenceError class may not be exported at the top level.
# We import it lazily for compatibility, but fall back to a generic Exception if unavailable.
try:
    from huggingface_hub import InferenceError  # type: ignore
except Exception:  # pragma: no cover
    InferenceError = Exception

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Constants
MAX_TOKENS = 2048
MODEL_ID = "codellama/CodeLlama-7b-Instruct-hf"
HF_TOKEN_ENV = "HF_TOKEN"
RETRY_LIMIT = 3
BACKOFF_BASE_SECONDS = 60  # exponential backoff base

def _load_validated_snippets() -> List[Dict]:
    """Load snippets from `data/validated_snippets.jsonl`."""
    input_path = paths.data("validated_snippets.jsonl")
    snippets: List[Dict] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            snippets.append(json.loads(line))
    log.info(f"Loaded {len(snippets)} validated snippets from {input_path}")
    return snippets

def _tokenizer():
    """Return a tiktoken tokenizer. Use cl100k_base which works well for code."""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback to the default encoding for models that may not have cl100k_base
        enc = tiktoken.encoding_for_model("gpt-4")
    return enc

def _truncate_to_token_limit(code: str, enc) -> str:
    """
    Truncate ``code`` so that its token count does not exceed ``MAX_TOKENS``.
    Truncation happens at line boundaries (nearest newline).
    Returns the possibly‑truncated code.
    """
    tokens = enc.encode(code)
    if len(tokens) <= MAX_TOKENS:
        return code

    # Split into lines and keep adding until limit would be exceeded
    lines = code.splitlines(keepends=True)
    kept_lines: List[str] = []
    for line in lines:
        prospective = "".join(kept_lines) + line
        if len(enc.encode(prospective)) > MAX_TOKENS:
            break
        kept_lines.append(line)

    truncated = "".join(kept_lines)
    if not truncated:
        # As a last resort keep the first line even if it exceeds limit
        truncated = lines[0]
    return truncated

def _log_truncation(snippet_id: str, original_len: int, truncated_len: int):
    """Append a truncation warning to the log file."""
    log_path = paths.data("truncation_warnings.log")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            f"snippet_id={snippet_id} original_tokens={original_len} "
            f"truncated_tokens={truncated_len}\n"
        )
    log.warning(
        f"Snippet {snippet_id} truncated from {original_len} to {truncated_len} tokens."
    )

def _generate_llm_comment(code: str) -> str:
    """
    Call the HuggingFace Inference API to generate a comment for ``code``.
    Deterministic decoding is enforced via temperature=0.0 and top_p=1.0.
    Retries with exponential backoff are applied on failure.
    """
    token = os.getenv(HF_TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"HuggingFace token not found in environment variable {HF_TOKEN_ENV}"
        )

    # Initialise the client with the model ID so we don't need to pass it on each call.
    client = InferenceClient(model=MODEL_ID, token=token)

    # Simple prompt asking for a concise comment
    prompt = (
        "Generate a concise, helpful comment for the following Python code.\n"
        "```python\n"
        f"{code}\n"
        "```\n"
        "Comment:"
    )

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            generated = client.text_generation(
                prompt,
                temperature=0.0,
                top_p=1.0,
                max_new_tokens=256,
                do_sample=False,
            )
            # The client may return a dict when `details=True` is used; in our case it returns a string.
            comment = generated.strip() if isinstance(generated, str) else str(generated).strip()
            return comment
        except (InferenceError, Exception) as e:
            if attempt == RETRY_LIMIT:
                log.error(
                    f"Failed to generate comment for snippet after {RETRY_LIMIT} attempts: {e}"
                )
                raise
            backoff = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            log.warning(
                f"Attempt {attempt} failed with error: {e}. Retrying in {backoff}s..."
            )
            time.sleep(backoff)

    # Should never reach here
    raise RuntimeError("Unexpected exit from retry loop in _generate_llm_comment")

def main() -> None:
    """Entry point for the comment‑generation script."""
    snippets = _load_validated_snippets()
    enc = _tokenizer()

    output_path = paths.data("llm_comments.jsonl")
    # Ensure output file is freshly created
    if output_path.exists():
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out_f:
        for snippet in snippets:
            snippet_id = snippet.get("snippet_id") or snippet.get("id")
            code = snippet.get("code")
            # Human comment may be stored under different keys depending on earlier steps
            human_comment = (
                snippet.get("human_comment")
                or snippet.get("docstring")
                or snippet.get("human_docstring")
                or ""
            )

            if snippet_id is None or code is None:
                raise ValueError(
                    f"Snippet missing required fields: {snippet!r}"
                )

            # Token‑limit handling
            original_token_len = len(enc.encode(code))
            if original_token_len > MAX_TOKENS:
                truncated_code = _truncate_to_token_limit(code, enc)
                truncated_token_len = len(enc.encode(truncated_code))
                _log_truncation(snippet_id, original_token_len, truncated_token_len)
            else:
                truncated_code = code

            # Generate LLM comment
            llm_comment = _generate_llm_comment(truncated_code)
            if not llm_comment:
                raise RuntimeError(
                    f"Generated empty comment for snippet {snippet_id}"
                )

            record = {
                "snippet_id": snippet_id,
                "code": code,
                "human_comment": human_comment,
                "llm_comment": llm_comment,
                "no_comment": "",
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    log.info(f"Wrote LLM comments for {len(snippets)} snippets to {output_path}")

if __name__ == "__main__":
    main()