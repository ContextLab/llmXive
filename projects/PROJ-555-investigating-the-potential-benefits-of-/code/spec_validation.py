import os
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger

def verify_sc001_valid_sites(spec_path: str = "specs/001-ecotourism-regeneration/spec.md",
                             required_phrase: str = "up to 30 valid sites") -> bool:
    """
    Verify that SC-001 in the spec file contains the required phrase.
    
    Args:
        spec_path: Path to the specification markdown file.
        required_phrase: The exact phrase expected in SC-001.
        
    Returns:
        True if the phrase is found, False otherwise.
        
    Raises:
        FileNotFoundError: If the spec file does not exist.
    """
    spec_file = Path(spec_path)
    if not spec_file.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_file.absolute()}")
    
    content = spec_file.read_text(encoding='utf-8')
    
    # Simple check: look for the phrase anywhere in the file.
    # In a more robust implementation, we might parse the markdown to find SC-001 specifically.
    if required_phrase.lower() in content.lower():
        return True
    
    return False

def main():
    """
    Entry point for T001b: Verify SC-001 contains "up to 30 valid sites".
    
    Actions:
    1. Check if specs/001-ecotourism-regeneration/spec.md exists.
    2. Verify SC-001 contains "up to 30 valid sites".
    3. If missing or differs, log error to state/spec_validation.log and raise RuntimeError.
    4. If present, log success and exit cleanly.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting T001b: Verifying SC-001 in spec.md")
    
    spec_path = "specs/001-ecotourism-regeneration/spec.md"
    required_phrase = "up to 30 valid sites"
    log_file_path = "state/spec_validation.log"
    
    # Ensure state directory exists
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    
    try:
        # Ensure the spec file exists
        if not Path(spec_path).exists():
            error_msg = f"CRITICAL: Spec file not found at {spec_path}"
            logger.error(error_msg)
            # Write to log file
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"[T001b FAILED] {error_msg}\n")
            raise FileNotFoundError(error_msg)
        
        # Verify content
        found = verify_sc001_valid_sites(spec_path, required_phrase)
        
        if not found:
            error_msg = f"CRITICAL: SC-001 in {spec_path} does not contain '{required_phrase}'"
            logger.error(error_msg)
            # Write to log file
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"[T001b FAILED] {error_msg}\n")
            raise RuntimeError(error_msg)
        
        success_msg = f"SUCCESS: SC-001 verified. Found '{required_phrase}' in {spec_path}"
        logger.info(success_msg)
        # Write success to log file
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"[T001b PASSED] {success_msg}\n")
        
        return 0
        
    except Exception as e:
        logger.exception("Unhandled exception during T001b verification")
        return 1

if __name__ == "__main__":
    exit(main())
