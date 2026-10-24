import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set

import tiktoken
from huggingface_hub import InferenceClient, InferenceError

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# -------------------------------------------------------------------------
# Configuration constants
# -------------------------------------------------------------------------
MAX_TOKENS = 2048
MODEL_ID = "codellama/CodeLlama-7b-Instruct-hf"
HF_TOKEN_ENV = "HF_TOKEN"
RETRY_LIMIT = 3
BACKOFF_BASE_SECONDS = 60  # exponential back‑off base
PROJECT_SEED = 42

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def _load_validated_snippets() -> List[Dict]:
    """Load snippets from `data/validated_snippets.jsonl`."""
    input_path = paths.data("validated_snippets.jsonl")
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file {input_path} not found. Run T001 first."
        )

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
    """Return a tiktoken tokenizer for code."""
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback – should never happen for the provided model
        return tiktoken.encoding_for_model("gpt-4")

def _truncate_to_token_limit(code: str, enc) -> str:
    """
    Truncate ``code`` so that its token count does not exceed ``MAX_TOKENS``.
    Truncation happens at line boundaries (nearest newline).
    """
    tokens = enc.encode(code)
    if len(tokens) <= MAX_TOKENS:
        return code

    lines = code.splitlines(keepends=True)
    kept_lines: List[str] = []
    for line in lines:
        prospective = "".join(kept_lines) + line
        if len(enc.encode(prospective)) > MAX_TOKENS:
            break
        kept_lines.append(line)

    truncated = "".join(kept_lines)

    # Safety fallback: if even the first line exceeds the limit,
    # hard‑truncate to the token limit.
    if not truncated and lines:
        truncated = enc.decode(enc.encode(code)[:MAX_TOKENS])

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
    Deterministic decoding is enforced via temperature=0.0, top_p=1.0,
    seed=42, and do_sample=False.
    """
    token = os.getenv(HF_TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"HuggingFace token not found in environment variable {HF_TOKEN_ENV}"
        )

    client = InferenceClient(model=MODEL_ID, token=token)

    # CodeLlama‑Instruct format
    prompt = (
        f"[INST] Generate a concise, helpful, and professional docstring‑style comment "
        f"for the following Python code. Provide only the comment text, no conversational filler.\n\n"
        f"```python\n{code}\n``` [/INST]"
    )

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            generated = client.text_generation(
                prompt,
                temperature=0.0,
                top_p=1.0,
                max_new_tokens=256,
                do_sample=False,
                seed=PROJECT_SEED,
            )
            comment = (
                generated.strip()
                if isinstance(generated, str)
                else str(generated).strip()
            )
            if not comment:
                raise ValueError("API returned an empty string")
            return comment
        except (InferenceError, Exception) as e:
            if attempt == RETRY_LIMIT:
                log.error(
                    f"Failed to generate comment after {RETRY_LIMIT} attempts for snippet: {e}"
                )
                raise
            backoff = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            log.warning(
                f"Attempt {attempt} failed for snippet (error: {e}). "
                f"Retrying in {backoff}s..."
            )
            time.sleep(backoff)

    # Should never reach here
    raise RuntimeError("Unexpected exit from retry loop")

def _load_checkpoint() -> Set[str]:
    """Load already‑processed snippet IDs from the checkpoint file."""
    checkpoint_path = paths.data("generation_checkpoint.json")
    if not checkpoint_path.exists():
        return set()
    try:
        with checkpoint_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    except Exception as e:
        log.error(f"Could not read checkpoint file: {e}")
        return set()

def _save_checkpoint(processed_ids: Set[str]) -> None:
    """Persist the set of processed IDs to the checkpoint file."""
    checkpoint_path = paths.data("generation_checkpoint.json")
    with checkpoint_path.open("w", encoding="utf-8") as f:
        json.dump({"processed_ids": list(processed_ids)}, f, ensure_ascii=False, indent=2)

def _append_excluded(snippet_id: str) -> None:
    """Record a snippet that could not be generated."""
    excluded_path = paths.data("excluded_llm_generation.json")
    # Keep the file as a simple JSON list
    if excluded_path.exists():
        try:
            with excluded_path.open("r", encoding="utf-8") as f:
                excluded = json.load(f)
        except Exception:
            excluded = []
    else:
        excluded = []

    if snippet_id not in excluded:
        excluded.append(snippet_id)
        with excluded_path.open("w", encoding="utf-8") as f:
            json.dump(excluded, f, ensure_ascii=False, indent=2)

# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------
def main() -> None:
    """Generate LLM comments for all validated snippets with checkpointing."""
    start_time = datetime.utcnow().isoformat()
    log_path = paths.data("generation.log")
    with log_path.open("a", encoding="utf-8") as log_f:
        log_f.write(f"=== Generation started at {start_time} UTC ===\n")

    snippets = _load_validated_snippets()
    enc = _tokenizer()

    # Prepare output files (append mode for resumability)
    llm_out_path = paths.data("llm_comments.jsonl")
    llm_out_path.parent.mkdir(parents=True, exist_ok=True)

    processed_ids = _load_checkpoint()
    total = len(snippets)
    successful = 0
    failed = 0

    # Open the output file in append mode – if we are resuming we keep existing lines.
    with llm_out_path.open("a", encoding="utf-8") as out_f:
        for snippet in snippets:
            snippet_id = snippet.get("snippet_id") or snippet.get("id")
            if snippet_id is None:
                log.error(f"Snippet missing ID: {snippet}")
                continue

            # Skip already processed snippets
            if snippet_id in processed_ids:
                continue

            code = snippet.get("code")
            human_comment = (
                snippet.get("human_comment")
                or snippet.get("docstring")
                or snippet.get("human_docstring")
                or ""
            )
            if code is None:
                log.error(f"Snippet {snippet_id} missing code field.")
                _append_excluded(snippet_id)
                processed_ids.add(snippet_id)
                continue

            # Truncate if needed
            original_token_len = len(enc.encode(code))
            if original_token_len > MAX_TOKENS:
                truncated_code = _truncate_to_token_limit(code, enc)
                truncated_token_len = len(enc.encode(truncated_code))
                _log_truncation(snippet_id, original_token_len, truncated_token_len)
            else:
                truncated_code = code

            # Attempt generation
            try:
                llm_comment = _generate_llm_comment(truncated_code)
            except Exception:
                # Record exclusion and move on
                _append_excluded(snippet_id)
                failed += 1
                processed_ids.add(snippet_id)
                # Update checkpoint after each attempt (even failures) so we don't retry forever
                _save_checkpoint(processed_ids)
                continue

            record = {
                "snippet_id": snippet_id,
                "code": code,
                "human_comment": human_comment,
                "llm_comment": llm_comment,
                "no_comment": "",
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            successful += 1
            processed_ids.add(snippet_id)

            # Persist checkpoint after each successful snippet
            _save_checkpoint(processed_ids)

    end_time = datetime.utcnow().isoformat()
    with log_path.open("a", encoding="utf-8") as log_f:
        log_f.write(
            f"=== Generation finished at {end_time} UTC ===\n"
            f"Total snippets: {total}\n"
            f"Successfully generated: {successful}\n"
            f"Failed (excluded): {failed}\n"
        )

    log.info(
        f"LLM comment generation completed – {successful} succeeded, {failed} failed."
    )

if __name__ == "__main__":
    main()
