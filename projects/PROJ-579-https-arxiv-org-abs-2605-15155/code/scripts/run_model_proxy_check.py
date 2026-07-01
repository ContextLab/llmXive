"""
Script to enforce and verify the model proxy configuration for SDAR training.

This script sets the SDAR_MODEL_PROXY environment variable to 'distilbert-base-uncased'
and executes the training script to verify that the proxy model is loaded successfully.
It writes a verification report to outputs/health/model_proxy_verification.json.
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
TRAIN_SCRIPT = PROJECT_ROOT / "external" / "SDAR" / "agent_system" / "train.py"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "health"
LOG_FILE = PROJECT_ROOT / "outputs" / "logs" / "train_raw.log"

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "outputs" / "logs").mkdir(parents=True, exist_ok=True)

def run_training_with_proxy():
    """Run the training script with the proxy model enforced."""
    env = os.environ.copy()
    # Enforce the proxy model
    env["SDAR_MODEL_PROXY"] = "distilbert-base-uncased"
    # Ensure CPU-only execution
    env["CUDA_VISIBLE_DEVICES"] = ""
    
    # Prepare command
    cmd = [
        sys.executable,
        str(TRAIN_SCRIPT),
        "--num_steps", "10",
        "--batch_size", "1",
        "--env", "alfworld",
        "--device", "cpu"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    print(f"Environment: SDAR_MODEL_PROXY={env['SDAR_MODEL_PROXY']}")
    
    start_time = time.time()
    try:
        # Run the training script, capturing output
        process = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for the 10-step run
        )
        
        elapsed = time.time() - start_time
        
        # Check if the script ran successfully
        success = process.returncode == 0
        
        # Check logs for proxy model confirmation
        output_text = process.stdout + process.stderr
        proxy_confirmed = "distilbert-base-uncased" in output_text.lower()
        
        # Write results
        result = {
            "success": success,
            "proxy_model": env["SDAR_MODEL_PROXY"],
            "proxy_confirmed_in_logs": proxy_confirmed,
            "return_code": process.returncode,
            "elapsed_seconds": elapsed,
            "log_sample": output_text[:1000] if output_text else "",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        output_file = OUTPUT_DIR / "model_proxy_verification.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\nVerification result written to: {output_file}")
        print(f"Proxy model '{env['SDAR_MODEL_PROXY']}' loaded: {'YES' if proxy_confirmed else 'NO'}")
        
        if not success:
            print(f"Training script failed with return code {process.returncode}")
            if process.stderr:
                print(f"Error output:\n{process.stderr}")
        
        return success and proxy_confirmed
        
    except subprocess.TimeoutExpired:
        print("Training script timed out after 300 seconds")
        result = {
            "success": False,
            "proxy_model": env["SDAR_MODEL_PROXY"],
            "proxy_confirmed_in_logs": False,
            "error": "Timeout",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        with open(OUTPUT_DIR / "model_proxy_verification.json", "w") as f:
            json.dump(result, f, indent=2)
        return False
    except Exception as e:
        print(f"Error running training script: {e}")
        result = {
            "success": False,
            "proxy_model": env["SDAR_MODEL_PROXY"],
            "proxy_confirmed_in_logs": False,
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        with open(OUTPUT_DIR / "model_proxy_verification.json", "w") as f:
            json.dump(result, f, indent=2)
        return False

def main():
    print("=" * 60)
    print("SDAR Model Proxy Verification")
    print("=" * 60)
    
    if not TRAIN_SCRIPT.exists():
        print(f"ERROR: Training script not found at {TRAIN_SCRIPT}")
        sys.exit(1)
        
    success = run_training_with_proxy()
    
    print("\n" + "=" * 60)
    if success:
        print("VERIFICATION PASSED: Proxy model configured and active.")
    else:
        print("VERIFICATION FAILED: Check logs for details.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()