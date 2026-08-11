import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd: list):
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    return result.returncode

def main():
    base_dir = Path(__file__).parent.parent
    os.chdir(base_dir)
    
    # 1. Power Analysis
    logger.info("Step 1: Running Power Analysis")
    run_command([sys.executable, "code/run_power_analysis.py"])
    
    # 2. Generate Parameter Sweep
    logger.info("Step 2: Building Parameter Sweep")
    run_command([sys.executable, "code/generate_data.py", "--sweep", "--out", "data/sweep/params.csv"])
    
    # 3. Generate Seed Map
    logger.info("Step 3: Generating Seed Map")
    run_command([sys.executable, "code/generate_seed_map.py"])
    
    # 4. Run Hypothesis Tests (T022/T024)
    logger.info("Step 4: Running Hypothesis Tests")
    run_command([sys.executable, "code/run_tests.py"])
    
    # 5. Analyze P-values (T029)
    logger.info("Step 5: Analyzing P-values (KS Statistics)")
    run_command([sys.executable, "code/analyze_pvalues.py"])
    
    # 6. Sensitivity Analysis (T031)
    logger.info("Step 6: Running Sensitivity Analysis")
    run_command([sys.executable, "code/sensitivity_analysis.py"])
    
    # 7. Generate Docs
    logger.info("Step 7: Generating Documentation")
    run_command([sys.executable, "code/docs_generator.py"])
    
    logger.info("Pipeline complete.")

if __name__ == '__main__':
    main()
