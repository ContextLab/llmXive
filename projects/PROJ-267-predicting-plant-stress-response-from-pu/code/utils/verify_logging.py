import sys
from pathlib import Path
from utils.logging_config import get_logger

def main():
    """
    Verification script to ensure T006 requirements are met:
    1. logs/pipeline.log is created.
    2. INFO and WARN messages are correctly written to the file.
    """
    # 1. Use the logger to write required messages
    logger = get_logger("T006_Verifier")
    
    info_msg = "T006: Initializing logging verification."
    warn_msg = "T006: This is a required warning message for verification."
    final_msg = "T006: Logging verification complete."
    
    logger.info(info_msg)
    logger.warning(warn_msg)
    logger.info(final_msg)

    # 2. Verify the artifact exists
    log_file = Path("logs/pipeline.log")
    if not log_file.exists():
        print("Error: logs/pipeline.log was not created.")
        sys.exit(1)

    # 3. Verify contents
    content = log_file.read_text()
    
    # Check for INFO level
    if info_msg not in content:
        print(f"Error: INFO message '{info_msg}' not found in log.")
        sys.exit(1)
    
    # Check for WARN level
    if warn_msg not in content:
        print(f"Error: WARNING message '{warn_msg}' not found in log.")
        sys.exit(1)
    
    if final_msg not in content:
        print(f"Error: Final INFO message '{final_msg}' not found in log.")
        sys.exit(1)

    print("Logging verification successful. logs/pipeline.log created and populated.")
    sys.exit(0)

if __name__ == "__main__":
    main()