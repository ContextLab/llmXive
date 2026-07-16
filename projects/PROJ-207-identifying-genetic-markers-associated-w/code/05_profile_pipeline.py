import cProfile
import pstats
import io
import sys
import os
import time
import importlib.util
from pathlib import Path

# Ensure we can import from code/ and code/utils
# We assume this script is run from the project root or code/
# If run from code/, we need to adjust the path
current_dir = Path(__file__).parent
root_dir = current_dir.parent if current_dir.name == "code" else current_dir
code_dir = root_dir / "code"
utils_dir = root_dir / "code" / "utils"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))
if str(utils_dir) not in sys.path:
    sys.path.insert(0, str(utils_dir))

# List of pipeline modules to profile
# These correspond to the main processing steps in the pipeline
PIPELINE_STEPS = [
    {"name": "generate_synthetic_data", "module": "00_generate_synthetic_data", "main_func": "main"},
    {"name": "generate_simulated_fastq", "module": "00_generate_simulated_fastq", "main_func": "main"},
    {"name": "align_call", "module": "02_align_call", "main_func": "main"},
    {"name": "vcf_to_plink", "module": "utils.vcf_to_plink", "main_func": "main"},
    {"name": "preprocess_phenotype", "module": "utils.preprocess_phenotype", "main_func": "main"},
    {"name": "gwas", "module": "03_gwas", "main_func": "main"},
    {"name": "fdr_correction", "module": "utils.fdr_correction", "main_func": "main"},
    {"name": "threshold_sensitivity", "module": "utils.threshold_sensitivity", "main_func": "main"},
    {"name": "ml_validation", "module": "04_ml_validation", "main_func": "main"},
    {"name": "annotation", "module": "05_annotation", "main_func": "main"},
]

def load_module_from_file(module_name, file_path):
    """Dynamically load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_pipeline_steps(profile_steps=True):
    """
    Execute the pipeline steps. If profile_steps is True, we will profile them.
    This function returns a list of (step_name, duration) tuples.
    """
    results = []
    
    # We need to simulate running the pipeline. 
    # Since we cannot run the full pipeline (external tools like bwa, freebayes, plink might not be installed),
    # we will profile the *logic* of the Python scripts that are part of the pipeline.
    # For shell scripts (02_align_call.sh, 03_gwas.sh), we cannot profile them with cProfile directly.
    # Instead, we will profile the Python wrappers or the core logic functions.
    
    # For this task, we will focus on profiling the Python modules that do the heavy lifting.
    # We will simulate the execution by calling the main functions with appropriate arguments
    # or by profiling the import and initialization if main requires external tools.
    
    # To make this robust, we will:
    # 1. Try to run the main function if it's a pure Python script.
    # 2. If it fails (e.g., missing external tools), we will profile the import and a dummy run.
    
    for step in PIPELINE_STEPS:
        module_name = step["module"]
        main_func_name = step["main_func"]
        step_name = step["name"]
        
        print(f"Profiling step: {step_name}")
        
        try:
            # Determine the file path
            if module_name.startswith("utils."):
                module_file = utils_dir / f"{module_name.replace('.', '/')}.py"
            else:
                module_file = code_dir / f"{module_name}.py"
            
            if not module_file.exists():
                print(f"  Skipping {step_name}: module file not found ({module_file})")
                results.append((step_name, 0.0, "Module not found"))
                continue
            
            # Load the module
            module = load_module_from_file(module_name, module_file)
            
            if not hasattr(module, main_func_name):
                print(f"  Skipping {step_name}: main function '{main_func_name}' not found")
                results.append((step_name, 0.0, "Main function not found"))
                continue
            
            main_func = getattr(module, main_func_name)
            
            # Profile the main function
            # We use a Profile object to capture stats
            pr = cProfile.Profile()
            pr.enable()
            
            start_time = time.time()
            
            try:
                # Attempt to run the main function
                # We might need to pass arguments, but for profiling, we can often run without or with defaults
                # If the function requires arguments, we might need to adjust.
                # For now, we assume main() takes no arguments or uses argparse which we can bypass for profiling
                # by mocking sys.argv or calling the underlying logic.
                # To be safe, we'll try calling main() and catch exceptions.
                main_func()
            except SystemExit:
                # Some scripts call sys.exit(), which is expected
                pass
            except Exception as e:
                print(f"  Warning: {step_name} raised an exception during profiling: {e}")
                # We still want to capture the profile up to the exception
            
            end_time = time.time()
            duration = end_time - start_time
            
            pr.disable()
            
            results.append((step_name, duration, "Completed"))
            print(f"  Completed {step_name} in {duration:.2f}s")
            
        except Exception as e:
            print(f"  Error profiling {step_name}: {e}")
            results.append((step_name, 0.0, f"Error: {e}"))

    return results

def write_profile_report(results, output_path):
    """
    Write the profile report to the specified output path.
    The report will include:
    - A summary of each step's execution time
    - A sorted list of functions by cumulative time (aggregated across all steps)
    """
    # We need to aggregate the profiles. Since we ran them separately, we'll just report the summary.
    # To get a combined profile, we would need to run them in a single cProfile context.
    # Let's refactor to run all steps in one profile session.
    pass

def main():
    """
    Main entry point for profiling the pipeline.
    """
    # Define output path
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "profile_report.txt"

    # We will profile all steps in a single cProfile run to get a global view
    pr = cProfile.Profile()
    pr.enable()

    start_time = time.time()
    
    # Run the pipeline steps
    # We'll create a list to store results for the report
    step_results = []

    for step in PIPELINE_STEPS:
        module_name = step["module"]
        main_func_name = step["main_func"]
        step_name = step["name"]
        
        step_start = time.time()
        status = "Completed"
        
        try:
            # Determine the file path
            if module_name.startswith("utils."):
                module_file = utils_dir / f"{module_name.replace('.', '/')}.py"
            else:
                module_file = code_dir / f"{module_name}.py"
            
            if not module_file.exists():
                status = "Module not found"
                step_results.append((step_name, time.time() - step_start, status))
                continue
            
            # Load the module
            module = load_module_from_file(module_name, module_file)
            
            if not hasattr(module, main_func_name):
                status = "Main function not found"
                step_results.append((step_name, time.time() - step_start, status))
                continue
            
            main_func = getattr(module, main_func_name)
            
            try:
                main_func()
            except SystemExit:
                pass
            except Exception as e:
                status = f"Exception: {e}"
        
        except Exception as e:
            status = f"Error: {e}"
        
        step_duration = time.time() - step_start
        step_results.append((step_name, step_duration, status))

    end_time = time.time()
    total_duration = end_time - start_time

    pr.disable()

    # Write the report
    with open(output_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("PIPELINE PROFILE REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total execution time: {total_duration:.2f} seconds\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("STEP EXECUTION TIMES\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Step Name':<30} {'Duration (s)':<15} {'Status':<20}\n")
        f.write("-" * 80 + "\n")
        
        for step_name, duration, status in step_results:
            f.write(f"{step_name:<30} {duration:<15.2f} {status:<20}\n")
        
        f.write("-" * 80 + "\n")
        f.write("TOP 20 FUNCTIONS BY CUMULATIVE TIME\n")
        f.write("-" * 80 + "\n")
        
        # Sort stats by cumulative time
        stats_stream = io.StringIO()
        ps = pstats.Stats(pr, stream=stats_stream)
        ps.sort_stats('cumulative')
        ps.print_stats(20)  # Print top 20
        
        # Read the sorted stats
        stats_content = stats_stream.getvalue()
        f.write(stats_content)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

    print(f"Profile report written to {output_path}")

if __name__ == "__main__":
    main()