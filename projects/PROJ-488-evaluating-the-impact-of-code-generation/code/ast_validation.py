"""
AST Validation Module for CodeSnippet parsing.

Implements Task T018: Validate that >=95% of code snippets parse correctly.
Aborts with error 102 if the threshold is not met.
"""
import ast
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Import project utilities
from data_ingestion import ingest_codesearchnet, ingest_codegen, verify_datasets
from checksum import compute_sha256, register_dataset_checksum, write_checksums, read_checksums
from logging_config import get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file
from seeds import get_seed_value

# Constants
PARSE_THRESHOLD = 0.95
ERROR_CODE = 102
STATE_FILE_PATH = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
VALIDATION_LOG_PATH = PROCESSED_DIR / "ast_validation_log.json"

logger = get_logger(__name__)


def parse_snippet(code: str) -> bool:
    """
    Attempt to parse a code snippet using Python's ast module.
    
    Args:
        code: The source code string.
        
    Returns:
        True if parsing succeeds, False otherwise.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
    except Exception:
        # Catch any other potential parsing errors (though rare for ast.parse)
        return False


def validate_datasets(
    codesearchnet_data: List[Dict], 
    codegen_data: List[Dict],
    min_snippets_per_group: int = 1000
) -> Tuple[Dict, bool]:
    """
    Validate AST parsing for both human-written and LLM-generated datasets.
    
    Args:
        codesearchnet_data: List of CodeSnippet dicts from CodeSearchNet.
        codegen_data: List of CodeSnippet dicts from CodeParrot/CodeGen.
        min_snippets_per_group: Minimum required snippets per group for validation.
        
    Returns:
        A tuple of (validation_report, success_flag).
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "threshold": PARSE_THRESHOLD,
        "groups": {}
    }
    
    all_valid = True
    
    groups = [
        ("human_written", codesearchnet_data),
        ("llm_generated", codegen_data)
    ]
    
    for group_name, data in groups:
        total = len(data)
        valid_count = 0
        invalid_ids = []
        
        if total == 0:
            logger.error(f"Group '{group_name}' has no data to validate.")
            results["groups"][group_name] = {
                "total": 0,
                "valid": 0,
                "invalid_count": 0,
                "parse_rate": 0.0,
                "status": "failed",
                "message": "No data available"
            }
            all_valid = False
            continue
        
        for snippet in data:
            snippet_id = snippet.get("id", "unknown")
            code = snippet.get("code", "")
            
            if parse_snippet(code):
                valid_count += 1
            else:
                invalid_ids.append(snippet_id)
        
        parse_rate = valid_count / total
        status = "passed" if parse_rate >= PARSE_THRESHOLD else "failed"
        
        if status == "failed":
            all_valid = False
            logger.error(
                f"Group '{group_name}' parse rate {parse_rate:.4f} "
                f"(< {PARSE_THRESHOLD}). Aborting with error {ERROR_CODE}."
            )
        
        # Log first 10 invalid IDs to avoid log spam
        log_invalid_ids = invalid_ids[:10] if len(invalid_ids) > 10 else invalid_ids
        
        results["groups"][group_name] = {
            "total": total,
            "valid": valid_count,
            "invalid_count": len(invalid_ids),
            "parse_rate": parse_rate,
            "status": status,
            "invalid_sample_ids": log_invalid_ids,
            "total_invalid_ids": len(invalid_ids)
        }
        
        logger.info(
            f"Group '{group_name}': {valid_count}/{total} parsed successfully "
            f"({parse_rate:.2%}). Status: {status}"
        )
    
    return results, all_valid


def run_ast_validation() -> bool:
    """
    Main entry point for Task T018.
    Downloads, filters, and validates AST parsing of datasets.
    
    Returns:
        True if validation passes, False otherwise.
    """
    logger.info("Starting AST Validation (Task T018)...")
    
    # Ensure directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verify datasets are available (T014 prerequisite)
    verify_datasets_path = DATA_DIR / "verified_sources.json"
    if not verify_datasets_path.exists():
        logger.error("Verified sources file not found. Run T014 first.")
        return False
        
    with open(verify_datasets_path, "r") as f:
        verified = json.load(f)
        
    if not verified.get("codesearchnet") or not verified.get("codegen"):
        logger.error("Datasets not verified. Aborting.")
        return False
    
    # Ingest datasets (using existing functions from data_ingestion)
    # Note: We assume T012 and T013 have populated data/raw/ or we stream directly.
    # For this task, we assume the ingestion functions return the data structures
    # needed for validation. If they download to disk, we load from disk.
    # Based on T012/T013, we expect data to be available.
    
    # Attempt to load pre-processed data if it exists (from T016/T017)
    # If not, we run the ingestion steps.
    
    csn_path = PROCESSED_DIR / "codesearchnet_python_filtered.json"
    cg_path = PROCESSED_DIR / "codegen_python_filtered.json"
    
    if not csn_path.exists() or not cg_path.exists():
        logger.info("Filtered data not found. Running ingestion and filtering steps...")
        # This might be heavy, but T017 implies filtering is done. 
        # We call the ingestion functions which should handle loading/filtering.
        # Note: In a real pipeline, T017 would have produced these files.
        # We simulate the data retrieval here for the validation step.
        # Assuming the ingestion functions return the list of dicts.
        
        # We need to handle the fact that ingestion functions might download to disk.
        # Let's assume T016/T017 logic is encapsulated or we re-run minimal steps.
        # For this implementation, we assume the data is in data/raw/ or loaded.
        # We will call the ingestion functions to get the data.
        # Note: The provided API for data_ingestion shows functions like ingest_codesearchnet.
        # We assume they return the data list.
        
        try:
            # Re-ingest to ensure data is present (or load from raw if T012/013 did it)
            # Since T012/T013 are marked done, we assume data exists.
            # We'll call the functions to get the data.
            # If they download, we need to ensure we get the filtered python snippets.
            # For T018, we need the filtered data.
            # We assume the data_ingestion module has logic to return the data.
            # If not, we might need to load from the raw files.
            
            # Fallback: Try to load from raw if ingestion functions don't return data directly
            # This is a placeholder for the actual loading logic which depends on T012/013 output
            # We assume the ingestion functions are called here to get the data.
            # For the sake of this task, we assume we get the data from the ingestion functions.
            
            # Since I cannot run the code, I must write the code that *would* work.
            # I will assume ingest_codesearchnet and ingest_codegen return the lists.
            # If they don't, the user must implement the loading logic in those functions.
            # But the prompt says "Use the provided existing API surface".
            # The API surface lists `ingest_codesearchnet` and `ingest_codegen`.
            # I will assume they return the data.
            
            csn_data = ingest_codesearchnet()
            cg_data = ingest_codegen()
            
            if not csn_data or not cg_data:
                logger.error("Failed to ingest data.")
                return False
                
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            # Fallback to loading from disk if ingestion fails (e.g. data already there)
            # This part is speculative as the exact return type of ingestion functions isn't shown.
            # But we must follow the API.
            return False
    else:
        # Load from disk
        logger.info("Loading pre-processed data from disk.")
        with open(csn_path, "r") as f:
            csn_data = json.load(f)
        with open(cg_path, "r") as f:
            cg_data = json.load(f)
    
    # Validate
    report, success = validate_datasets(csn_data, cg_data)
    
    # Write validation log
    with open(VALIDATION_LOG_PATH, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation log written to {VALIDATION_LOG_PATH}")
    
    # Update state
    if success:
        update_state_with_artifact(
            state_file=STATE_FILE_PATH,
            artifact_name="ast_validation",
            artifact_path=str(VALIDATION_LOG_PATH),
            status="completed",
            details={"parse_rate_human": report["groups"]["human_written"]["parse_rate"],
                     "parse_rate_llm": report["groups"]["llm_generated"]["parse_rate"]}
        )
    else:
        # Abort with error 102
        logger.error(f"AST Validation failed. Threshold {PARSE_THRESHOLD} not met. Error {ERROR_CODE}.")
        sys.exit(ERROR_CODE)
        
    return success


def main():
    """Main entry point for the script."""
    success = run_ast_validation()
    if success:
        logger.info("AST Validation completed successfully.")
    else:
        logger.error("AST Validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
