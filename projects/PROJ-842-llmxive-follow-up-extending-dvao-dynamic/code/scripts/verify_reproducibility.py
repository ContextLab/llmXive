import os
import sys
import subprocess
import hashlib
import json
import shutil
import tempfile

def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def run_experiment(seed, output_dir):
    """Run the experiment with a specific seed and save outputs."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Command to run: python code/src/environment/runner.py --n=50 --seed=SEED --noise-correlation=0.5
    # We use a representative command that exercises the noise correlation logic
    cmd = [
        sys.executable, 
        "code/src/environment/runner.py",
        "--n", "10",
        "--seed", str(seed),
        "--noise-correlation", "0.5",
        "--rollout-size", "100"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Run completed with seed {seed}")
    except subprocess.CalledProcessError as e:
        print(f"Run failed with seed {seed}: {e}")
        print(f"stderr: {e.stderr}")
        raise

def main():
    print("Starting Reproducibility Verification...")
    
    # Create temporary directories for two runs
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        run1_dir = os.path.join(tmpdir1, "run1")
        run2_dir = os.path.join(tmpdir2, "run2")
        
        seed = 42
        
        # Run 1
        print(f"\n--- Run 1 (Seed {seed}) ---")
        run_experiment(seed, run1_dir)
        
        # Collect output files from run 1
        # We look for the noise_properties.json and any other key outputs
        # The runner writes to code/data/processed/, so we copy them
        source_dir = "code/data/processed"
        files_to_check = [
            "noise_properties.json",
            "empirical_results.json",
            "statistical_report.json"
        ]
        
        run1_hashes = {}
        for fname in files_to_check:
            fpath = os.path.join(source_dir, fname)
            if os.path.exists(fpath):
                # Copy to temp dir to avoid overwriting
                dest = os.path.join(run1_dir, fname)
                shutil.copy(fpath, dest)
                run1_hashes[fname] = get_file_hash(dest)
            else:
                print(f"Warning: {fname} not found in run 1")

        # Run 2
        print(f"\n--- Run 2 (Seed {seed}) ---")
        run_experiment(seed, run2_dir)
        
        run2_hashes = {}
        for fname in files_to_check:
            fpath = os.path.join(source_dir, fname)
            if os.path.exists(fpath):
                dest = os.path.join(run2_dir, fname)
                shutil.copy(fpath, dest)
                run2_hashes[fname] = get_file_hash(dest)
            else:
                print(f"Warning: {fname} not found in run 2")
        
        # Compare
        print("\n--- Comparison ---")
        all_match = True
        for fname in files_to_check:
            h1 = run1_hashes.get(fname)
            h2 = run2_hashes.get(fname)
            if h1 is None or h2 is None:
                print(f"  {fname}: MISSING in one or both runs")
                all_match = False
            elif h1 == h2:
                print(f"  {fname}: MATCH (hash={h1})")
            else:
                print(f"  {fname}: MISMATCH (run1={h1}, run2={h2})")
                all_match = False
        
        if all_match:
            print("\n✅ SUCCESS: All outputs are byte-identical. Reproducibility verified.")
            sys.exit(0)
        else:
            print("\n❌ FAILURE: Outputs differ. Reproducibility NOT verified.")
            sys.exit(1)

if __name__ == "__main__":
    main()