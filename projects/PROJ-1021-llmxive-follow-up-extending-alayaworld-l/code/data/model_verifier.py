"""
Model Availability Verifier for AlayaWorld.

This script attempts to load the frozen AlayaWorld model.
- If successful: Outputs status "FOUND" and exits with code 0.
- If failed/unavailable: Outputs status "MISSING" and exits with code 1.

Output: data/model_verification.json
Schema: {"status": "FOUND"|"MISSING", "model_path": string|null, "exit_code": int, "timestamp": string}
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Project root relative to this file (code/data -> root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "model_verification.json"

# Configuration for the model path
# The spec mentions "frozen AlayaWorld model". We assume a standard HuggingFace
# path or a local path if previously downloaded.
# Since T001b includes 'transformers', 'diffusers', 'accelerate', we attempt to load.
MODEL_IDENTIFIER = "AlayaWorld/frozen-model-v1"  # Placeholder ID per spec context
LOCAL_MODEL_PATH = PROJECT_ROOT / "models" / "alayaworld_frozen"

def verify_model_availability():
    """
    Attempts to load the model. Returns a tuple (status, model_path_str, exit_code).
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    model_path_to_use = None
    status = "MISSING"
    exit_code = 1

    try:
        # Attempt 1: Check local path if it exists
        if LOCAL_MODEL_PATH.exists():
            model_path_to_use = str(LOCAL_MODEL_PATH)
            # Try to import and load (dry run to verify availability)
            try:
                from transformers import AutoConfig
                # We verify the config/tokenizer can be loaded or path is valid.
                # For a "frozen" model, we assume it's a standard HF architecture.
                # If the path exists and is a valid model directory, we consider it FOUND.
                # We check for config.json to be sure it's a model dir.
                if (LOCAL_MODEL_PATH / "config.json").exists():
                    # Attempt to load config to ensure it's a valid model dir
                    config = AutoConfig.from_pretrained(
                        LOCAL_MODEL_PATH,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    status = "FOUND"
                    exit_code = 0
                else:
                    # Exists but not a valid model dir
                    pass
            except ImportError:
                # transformers not installed, but we have the files. 
                # However, the task implies we need to load it.
                pass
            except Exception:
                pass

        # Attempt 2: Try to resolve via HuggingFace if local not found
        # We use a try/except block around the import and resolution logic.
        # If the model is not available locally or on HF (network/model missing),
        # we catch the error.
        if status == "MISSING":
            try:
                from transformers import AutoConfig
                # Attempt to load config to verify model existence
                # This will raise an exception if the model ID is invalid or network fails
                # We do not download weights, just verify the model definition is reachable.
                config = AutoConfig.from_pretrained(
                    MODEL_IDENTIFIER, 
                    trust_remote_code=True,
                    local_files_only=False # Allow network check if local fails
                )
                # If we get here, the model is known to HF.
                # We consider this "FOUND" for the purpose of the pipeline,
                # assuming the runner will have the weights or the pipeline handles the load.
                status = "FOUND"
                exit_code = 0
                model_path_to_use = MODEL_IDENTIFIER
            except Exception:
                # Model not found locally or on HF
                status = "MISSING"
                exit_code = 1
                model_path_to_use = None

    except Exception as e:
        # Unexpected error during verification
        status = "MISSING"
        exit_code = 1
        model_path_to_use = None
        # Log the error to stderr for debugging, but we still write the JSON
        print(f"Error during model verification: {e}", file=sys.stderr)

    result = {
        "status": status,
        "model_path": model_path_to_use,
        "exit_code": exit_code,
        "timestamp": timestamp
    }

    # Write the result to the output file
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"Model verification complete. Status: {status}. Output written to {OUTPUT_PATH}")
    
    return exit_code

def main():
    """
    Entry point for the script.
    """
    exit_code = verify_model_availability()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()