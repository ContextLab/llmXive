import json
import os
import time
from pathlib import Path
from typing import List, Dict

import tiktoken
from huggingface_hub import InferenceClient
try:
    from huggingface_hub import InferenceError
except ImportError:
    InferenceError = Exception

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Constants
MAX_TOKENS = 2048
MODEL_ID = "codellama/CodeLlama-7b-Instruct-hf"
HF_TOKEN_ENV = "HF_TOKEN"
RETRY_LIMIT = 3
BACKOFF_BASE_SECONDS = 60

def _load_validated_snippets() -> List[Dict]:
    """Load snippets from `data/validated_snippets.jsonl`."""
    input_path = paths.data("validated_snippets.jsonl")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} not found. Run T001 first.")
    
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
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
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
    if not truncated and lines:
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
    log.warning(f"Snippet {snippet_id} truncated from {original_len} to {truncated_len} tokens.")

def _generate_llm_comment(code: str) -> str:
    """
    Call the HuggingFace Inference API to generate a comment for ``code``.
    Deterministic decoding is enforced via temperature=0.0 and top_p=1.0.
    """
    token = os.getenv(HF_TOKEN_ENV)
    if not token:
        raise RuntimeError(f"HuggingFace token not found in environment variable {HF_TOKEN_ENV}")

    client = InferenceClient(model=MODEL_ID, token=token)

    # CodeLlama-Instruct format: [INST] prompt [/INST]
    prompt = (
        f"[INST] Generate a concise, helpful, and professional docstring-style comment "
        f"for the following Python code. Provide only the comment text, no conversational filler.\n\n"
        f"```python\n{code}\n``` [/INST]"
    )

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            # temperature=0.0 and top_p=1.0 ensure deterministic greedy decoding.
            generated = client.text_generation(
                prompt,
                temperature=0.0,
                top_p=1.0,
                max_new_tokens=256,
                do_sample=False,
            )
            comment = generated.strip() if isinstance(generated, str) else str(generated).strip()
            if not comment:
                raise ValueError("API returned an empty string")
            return comment
        except (InferenceError, Exception) as e:
            if attempt == RETRY_LIMIT:
                log.error(f"Failed to generate comment after {RETRY_LIMIT} attempts: {e}")
                raise
            backoff = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            log.warning(f"Attempt {attempt} failed: {e}. Retrying in {backoff}s...")
            time.sleep(backoff)

    raise RuntimeError("Unexpected exit from retry loop")

def main() -> None:
    """Entry point for the comment-generation script."""
    snippets = _load_validated_snippets()
    enc = _tokenizer()

    output_path = paths.data("llm_comments.jsonl")
    if output_path.exists():
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out_f:
        for snippet in snippets:
            snippet_id = snippet.get("snippet_id") or snippet.get("id")
            code = snippet.get("code")
            human_comment = (
                snippet.get("human_comment")
                or snippet.get("docstring")
                or snippet.get("human_docstring")
                or ""
            )

            if snippet_id is None or code is None:
                raise ValueError(f"Snippet missing required fields: {snippet!r}")

            original_token_len = len(enc.encode(code))
            if original_token_len > MAX_TOKENS:
                truncated_code = _truncate_to_token_limit(code, enc)
                truncated_token_len = len(enc.encode(truncated_code))
                _log_truncation(snippet_id, original_token_len, truncated_token_len)
            else:
                truncated_code = code

            llm_comment = _generate_llm_comment(truncated_code)

            record = {
                "snippet_id": snippet_id,
                "code": code,
                "human_comment": human_comment,
                "llm_comment": llm_comment,
                "no_comment": "",
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    log.info(f"Successfully wrote LLM comments for {len(snippets)} snippets to {output_path}")

if __name__ == "__main__":
    main()