import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from oracle.parser import parse_qwen_agentworld, QwenAgentWorldParser
from utils.checksums import check_code_drift, generate_checksum_manifest, verify_file_checksum

# Configure module logger
logger = logging.getLogger(__name__)

def build_oracle_graph(source_dir: str) -> Dict[str, Any]:
    """
    Parse Qwen-AgentWorld source code and build a deterministic state-transition oracle.
    
    Args:
        source_dir: Path to the Qwen-AgentWorld source code directory.
        
    Returns:
        A dictionary representing the Oracle Graph (nodes, edges, metadata).
    """
    logger.info(f"Starting Oracle Graph construction from source: {source_dir}")
    
    source_path = Path(source_dir)
    if not source_path.exists():
        logger.error(f"Source directory does not exist: {source_path}")
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    try:
        parser = QwenAgentWorldParser()
        logger.info("Initialized QwenAgentWorldParser")
        
        # Parse the source code to extract interaction logic
        parsed_data = parse_qwen_agentworld(source_path, parser)
        logger.info(f"Parsed {len(parsed_data.get('states', []))} states and "
                    f"{len(parsed_data.get('transitions', []))} transitions")
        
        oracle_graph = {
            "metadata": {
                "source": str(source_path),
                "parser_version": "1.0.0",
                "node_count": len(parsed_data.get('states', [])),
                "edge_count": len(parsed_data.get('transitions', []))
            },
            "states": parsed_data.get('states', []),
            "transitions": parsed_data.get('transitions', []),
            "rules": parsed_data.get('rules', [])
        }
        
        logger.info("Oracle Graph construction completed successfully")
        return oracle_graph

    except Exception as e:
        logger.exception(f"Failed to build Oracle Graph: {e}")
        raise

def save_and_verify(
    oracle_graph: Dict[str, Any],
    output_path: str,
    checksum_path: str
) -> bool:
    """
    Save the Oracle Graph to disk and verify its integrity via checksum.
    
    Args:
        oracle_graph: The dictionary representing the Oracle Graph.
        output_path: Path where the JSON file will be saved.
        checksum_path: Path where the checksum manifest will be saved.
        
    Returns:
        True if save and verification succeed, False otherwise.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving Oracle Graph to: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(oracle_graph, f, indent=2, sort_keys=True)
        logger.info(f"Successfully saved Oracle Graph to {output_file}")
    except IOError as e:
        logger.error(f"Failed to write Oracle Graph to {output_file}: {e}")
        return False

    # Generate checksum manifest
    logger.info("Generating checksum manifest...")
    try:
        manifest = generate_checksum_manifest([output_file])
        manifest_path = Path(checksum_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest saved to {manifest_path}")
    except Exception as e:
        logger.exception(f"Failed to generate checksum manifest: {e}")
        return False

    # Verify the saved file against the manifest
    logger.info("Verifying file integrity...")
    try:
        is_valid = verify_file_checksum(output_file, manifest)
        if is_valid:
            logger.info("Oracle Graph integrity verification PASSED.")
        else:
            logger.error("Oracle Graph integrity verification FAILED.")
            return False
    except Exception as e:
        logger.exception(f"Checksum verification error: {e}")
        return False

    # Check for code drift (compare source hash if available in manifest)
    # Assuming the manifest or a separate mechanism tracks source hashes
    logger.info("Performing Code Drift check...")
    try:
        # This is a placeholder for the actual drift check logic
        # In a real scenario, we might compare the hash of the source files
        # used to generate this against a stored baseline.
        # For now, we log the intent and assume check_code_drift handles it.
        drift_check = check_code_drift([output_file], manifest)
        if drift_check:
            logger.info("Code Drift check PASSED: No unexpected changes detected.")
        else:
            logger.warning("Code Drift check WARNING: Potential drift detected.")
            # Depending on policy, this might return False, but we allow warning
    except Exception as e:
        logger.exception(f"Code Drift check error: {e}")
        # Non-fatal for this step, but log it

    return True

def main():
    """
    Entry point for Oracle generation.
    Expects environment variables or command line args for paths.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Default paths (can be overridden by env vars or CLI in a full implementation)
    source_dir = Path("data/raw/qwen_agentworld_source")
    output_file = Path("data/processed/oracle_graph.json")
    checksum_file = Path("data/processed/oracle_graph.json.sha256")

    logger.info("="*50)
    logger.info("Starting Oracle Generation Pipeline")
    logger.info("="*50)

    try:
        # Step 1: Build Graph
        oracle_graph = build_oracle_graph(str(source_dir))
        
        # Step 2: Save and Verify
        success = save_and_verify(
            oracle_graph,
            str(output_file),
            str(checksum_file)
        )
        
        if success:
            logger.info("="*50)
            logger.info("Oracle Generation Pipeline COMPLETED SUCCESSFULLY")
            logger.info("="*50)
            return 0
        else:
            logger.error("="*50)
            logger.error("Oracle Generation Pipeline FAILED during verification")
            logger.error("="*50)
            return 1

    except Exception as e:
        logger.exception("Unhandled exception in Oracle Generation Pipeline")
        return 1

if __name__ == "__main__":
    sys.exit(main())