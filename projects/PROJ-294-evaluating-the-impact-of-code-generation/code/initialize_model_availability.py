import os
import json
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

def initialize_model_availability_file(output_path: str) -> None:
    """
    Initialize the state/model_availability.json file with default availability status.
    
    This task (T028c) prepares the state file required for sensitivity analysis (US1).
    It creates a JSON structure indicating that no models have been checked yet.
    """
    # Ensure the state directory exists
    state_dir = os.path.dirname(output_path)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir, exist_ok=True)

    initial_data = {
        "initialized_at": datetime.utcnow().isoformat() + "Z",
        "task_id": os.environ.get("TASK_ID", get_unique_id()),
        "models": {
            "Salesforce/codegen-mono": {
                "status": "uninitialized",
                "last_checked": None,
                "availability": None
            },
            "CodeLlama-7B": {
                "status": "uninitialized",
                "last_checked": None,
                "availability": None
            },
            "CodeLlama-3B": {
                "status": "uninitialized",
                "last_checked": None,
                "availability": None
            }
        },
        "api_status": {
            "hf_inference_api": "unknown",
            "last_check": None
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=2)

    logging.info(f"Initialized model availability state at {output_path}")

def main():
    """Main entry point for T028c."""
    setup_logging()
    set_task_id("T028c")
    logger = get_logger()
    
    output_path = "state/model_availability.json"
    
    try:
        initialize_model_availability_file(output_path)
        logger.info("T028c completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize model availability file: {e}")
        raise

if __name__ == "__main__":
    main()
