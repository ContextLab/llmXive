import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from oracle.parser import parse_qwen_agentworld, QwenAgentWorldParser
from utils.checksums import check_code_drift, generate_checksum_manifest, verify_file_checksum

# Configure logger for this module
logger = logging.getLogger(__name__)

def build_oracle_graph(source_dir: Path) -> Dict[str, Any]:
    """
    Parse the Qwen-AgentWorld source code and build the deterministic
    state-transition oracle graph.
    """
    logger.info(f"Starting Oracle Graph construction from source: {source_dir}")
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    try:
        # Parse the source code to extract interaction logic
        parser = QwenAgentWorldParser()
        parsed_data = parse_qwen_agentworld(source_dir, parser)
        
        if not parsed_data:
            logger.warning("No interaction logic found in source directory.")
            return {"nodes": [], "edges": [], "metadata": {"source": str(source_dir), "status": "empty"}}

        logger.info(f"Successfully parsed {len(parsed_data.get('nodes', []))} nodes and {len(parsed_data.get('edges', []))} edges.")
        return parsed_data
    except Exception as e:
        logger.error(f"Failed to build oracle graph: {e}", exc_info=True)
        raise

def save_and_verify(graph_data: Dict[str, Any], output_path: Path, checksum_manifest_path: Path) -> bool:
    """
    Save the generated oracle graph to JSON and perform checksum verification.
    Returns True if verification passes, False otherwise.
    """
    logger.info(f"Saving Oracle Graph to: {output_path}")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, default=str)
        logger.info("Oracle Graph saved successfully.")
    except IOError as e:
        logger.error(f"Failed to write Oracle Graph file: {e}", exc_info=True)
        raise

    # Perform checksum verification (Code Drift check)
    logger.info("Initiating checksum verification for Code Drift check...")
    try:
        manifest = generate_checksum_manifest([output_path])
        with open(checksum_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        # Verify the saved file against the manifest
        is_valid = verify_file_checksum(output_path, manifest)
        
        if is_valid:
            logger.info("Checksum verification passed. No code drift detected.")
        else:
            logger.error("Checksum verification failed. Potential code drift detected.")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Checksum verification error: {e}", exc_info=True)
        raise

def main():
    """
    Main entry point for Oracle generation and validation.
    """
    # Setup logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/oracle_generation.log", mode='a')
        ]
    )
    
    logger.info("=== Oracle Generation Pipeline Started ===")
    
    # Define paths (adjust based on project structure)
    source_dir = Path("data/raw/qwen_agentworld_source") # Placeholder, ensure this exists or is passed
    output_file = Path("data/processed/oracle_graph.json")
    checksum_file = Path("data/processed/oracle_checksums.json")

    # Allow overrides via CLI args if needed, defaulting for now
    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    if len(sys.argv) > 3:
        checksum_file = Path(sys.argv[3])

    logger.info(f"Configuration: Source={source_dir}, Output={output_file}, Checksum={checksum_file}")

    try:
        # 1. Build the Oracle Graph
        graph_data = build_oracle_graph(source_dir)
        
        # 2. Save and Verify
        success = save_and_verify(graph_data, output_file, checksum_file)
        
        if success:
            logger.info("=== Oracle Generation Pipeline Completed Successfully ===")
            return 0
        else:
            logger.error("=== Oracle Generation Pipeline Failed Verification ===")
            return 1
    except Exception as e:
        logger.critical(f"=== Oracle Generation Pipeline Fatal Error: {e} ===", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
