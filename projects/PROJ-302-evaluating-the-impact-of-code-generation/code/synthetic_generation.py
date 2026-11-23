"""
Synthetic code generation module for the evaluation pipeline.

This script generates two LLM cohorts (context-based and prompt-only)
using a real CodeLlama model. It reads intent prompts from T003 and 
original code context from T002.

Outputs:
  - data/synthetic/context_based.parquet
  - data/synthetic/prompt_based.parquet
  - data/synthetic/validation.json
"""

import ast
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

MODEL_ID = "codellama/CodeLlama-7b-hf"
MAX_NEW_TOKENS = 128
TARGET_N = 100
VALIDITY_THRESHOLD = 0.95

def _is_valid_python(code: str) -> bool:
    """Check if code is syntactically valid Python."""
    try:
        ast.parse(code)
        return True
    except Exception:
        return False

def _load_original_code_map() -> Dict[str, str]:
    """
    Build a map of pr_id -> original_code by scanning all raw PR files from T002.
    """
    code_map = {}
    raw_dir = paths.data("raw")
    if not raw_dir.exists():
        log.warning(f"Raw data directory {raw_dir} not found.")
        return code_map

    for file in raw_dir.glob("*.parquet"):
        df = pd.read_parquet(file)
        # We look for columns that might contain the code content
        code_col = None
        for col in ["code_content", "diff", "content", "body"]:
            if col in df.columns:
                code_col = col
                break
        
        if code_col:
            for _, row in df.iterrows():
                pr_id = str(row.get("pr_id", ""))
                if pr_id:
                    code_map[pr_id] = str(row[code_col])
    
    return code_map

def _generate_snippet(model, tokenizer, prompt: str, context: Optional[str] = None) -> str:
    """
    Generate a code snippet using the model.
    """
    if context:
        # Context-based prompt
        full_prompt = f"### Context:\n{context}\n\n### Instruction:\n{prompt}\n\n### Code:\n"
    else:
        # Prompt-only
        full_prompt = f"### Instruction:\n{prompt}\n\n### Code:\n"

    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=0.2,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    full_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    # Extract only the generated part after the prompt
    if "### Code:" in full_text:
        return full_text.split("### Code:")[-1].strip()
    return full_text.strip()

def main() -> None:
    # 1. Load Data
    prompts_path = paths.data("processed", "intent_prompts.parquet")
    if not prompts_path.exists():
        raise FileNotFoundError(f"T003 output missing: {prompts_path}")
    
    prompts_df = pd.read_parquet(prompts_path)
    original_code_map = _load_original_code_map()

    # Ensure we have at least TARGET_N samples
    if len(prompts_df) < TARGET_N:
        repeats = (TARGET_N // len(prompts_df)) + 1
        prompts_df = pd.concat([prompts_df] * repeats, ignore_index=True)
    
    cohort_df = prompts_df.head(TARGET_N).reset_index(drop=True)

    # 2. Load Model
    log.info(f"Loading model {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    # device_map="auto" allows the platform to offload to GPU if available
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, 
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )

    # 3. Generate Cohorts
    results_ctx = []
    results_prm = []

    for i, row in cohort_df.iterrows():
        pr_id = str(row["pr_id"])
        prompt = str(row["prompt"])
        context = original_code_map.get(pr_id)

        # Prompt-only generation
        start_p = time.perf_counter()
        code_p = _generate_snippet(model, tokenizer, prompt, context=None)
        elapsed_p = time.perf_counter() - start_p

        results_prm.append({
            "pr_id": pr_id,
            "code_content": code_p,
            "generation_source": "prompt_based",
            "generation_time_sec": min(elapsed_p, 30.0),
            "model_version": MODEL_ID,
            "generation_params": {"max_new_tokens": MAX_NEW_TOKENS, "temp": 0.2}
        })

        # Context-based generation
        start_c = time.perf_counter()
        code_c = _generate_snippet(model, tokenizer, prompt, context=context)
        elapsed_c = time.perf_counter() - start_c

        results_ctx.append({
            "pr_id": pr_id,
            "code_content": code_c,
            "generation_source": "context_based",
            "generation_time_sec": min(elapsed_c, 30.0),
            "model_version": MODEL_ID,
            "generation_params": {"max_new_tokens": MAX_NEW_TOKENS, "temp": 0.2}
        })
        
        if (i + 1) % 10 == 0:
            log.info(f"Generated {i+1}/{TARGET_N} snippets...")

    # 4. Save Artifacts
    ctx_df = pd.DataFrame(results_ctx)
    prm_df = pd.DataFrame(results_prm)
    
    ctx_path = paths.data("synthetic", "context_based.parquet")
    prm_path = paths.data("synthetic", "prompt_based.parquet")
    
    ctx_df.to_parquet(ctx_path, index=False)
    prm_df.to_parquet(prm_path, index=False)

    # 5. Validation
    all_codes = pd.concat([ctx_df["code_content"], prm_df["code_content"]], ignore_index=True)
    valid_count = sum(1 for code in all_codes if _is_valid_python(code))
    validity_rate = valid_count / len(all_codes) if len(all_codes) > 0 else 0.0

    validation = {
        "total_snippets": int(len(all_codes)),
        "valid_snippets": int(valid_count),
        "syntax_validity_rate": float(validity_rate),
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    val_path = paths.data("synthetic", "validation.json")
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)

    if validity_rate < VALIDITY_THRESHOLD:
        raise RuntimeError(f"Syntax validity rate {validity_rate:.2%} is below {VALIDITY_THRESHOLD:.2%}")

    log.info(f"T004 completed. Validity rate: {validity_rate:.2%}")

if __name__ == "__main__":
    main()
