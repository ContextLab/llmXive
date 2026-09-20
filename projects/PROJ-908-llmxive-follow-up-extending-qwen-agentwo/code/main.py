import logging
import sys
from pathlib import Path

from oracle.generator import build_oracle_graph, save_and_verify
from utils.checksums import check_code_drift, generate_checksum_manifest, verify_file_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

def main():
    logger.info("Starting llmXive pipeline execution...")
    
    # 1. Check for code drift before proceeding
    code_dir = Path(__file__).parent
    if not check_code_drift(code_dir):
        logger.error("Code drift detected. Aborting execution.")
        sys.exit(1)
    
    # 2. Generate Manifest for current state
    generate_checksum_manifest(code_dir)

    # 3. Build Oracle
    logger.info("Building Ground Truth Oracle...")
    # Assuming default paths based on project structure
    source_code_path = code_dir / "oracle" # Placeholder for actual source path
    oracle_graph = build_oracle_graph(source_code_path)
    
    # 4. Save and Verify
    output_path = Path("data/processed")
    output_path.mkdir(parents=True, exist_ok=True)
    oracle_file = output_path / "oracle_graph.json"
    
    save_and_verify(oracle_graph, oracle_file)
    
    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()
