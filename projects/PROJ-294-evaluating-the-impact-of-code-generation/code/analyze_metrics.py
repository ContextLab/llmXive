import os
import json
import logging
import subprocess
import tempfile
import sys
from typing import Dict, List, Any, Optional
from radon.complexity import cc_visit
from radon.metrics import h_visit
import xml.etree.ElementTree as ET

def load_test_suites(code_samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return code_samples

def calculate_code_metrics(code: str) -> Dict[str, Any]:
    try:
        # Cyclomatic Complexity
        complexity_blocks = cc_visit(code)
        cc_max = max([b.complexity for b in complexity_blocks], default=0)
        cc_average = sum([b.complexity for b in complexity_blocks]) / len(complexity_blocks) if complexity_blocks else 0

        # Halstead Metrics
        halstead_metrics = h_visit(code)
        halstead_volume = halstead_metrics[0].volume if halstead_metrics else 0

        return {
            "cyclomatic_complexity": cc_max,
            "halstead_volume": halstead_volume
        }
    except Exception as e:
        logging.error(f"Error calculating metrics: {e}")
        return {"cyclomatic_complexity": -1, "halstead_volume": -1}

def execute_test_suite(code: str, test_code: str) -> bool:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.write("\n\n")
        f.write(test_code)
        temp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False
    finally:
        os.unlink(temp_path)

def execute_coverage_test(code: str, test_code: str) -> Optional[float]:
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "module.py")
        test_path = os.path.join(tmpdir, "test_module.py")
        
        with open(code_path, "w") as f:
            f.write(code)
        
        with open(test_path, "w") as f:
            f.write(test_code)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--cov=module", "--cov-report=xml", test_path],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=30
            )
            
            xml_path = os.path.join(tmpdir, "coverage.xml")
            if os.path.exists(xml_path):
                tree = ET.parse(xml_path)
                root = tree.getroot()
                branch_coverage = float(root.get("branch-rate", 0)) * 100
                return branch_coverage
            return None
        except Exception:
            return None

def analyze_batch_metrics(code_samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for sample in code_samples:
        if sample.get("status") != "success" or not sample.get("generated_code"):
            results.append({
                "task_id": sample["task_id"],
                "cyclomatic_complexity": -1,
                "halstead_volume": -1,
                "pass_rate": -1,
                "branch_coverage_pct": -1
            })
            continue

        code = sample["generated_code"]
        test_code = sample.get("test", "")
        
        metrics = calculate_code_metrics(code)
        pass_rate = 1 if execute_test_suite(code, test_code) else 0
        branch_coverage = execute_coverage_test(code, test_code)
        
        results.append({
            "task_id": sample["task_id"],
            "cyclomatic_complexity": metrics["cyclomatic_complexity"],
            "halstead_volume": metrics["halstead_volume"],
            "pass_rate": pass_rate,
            "branch_coverage_pct": branch_coverage if branch_coverage is not None else -1
        })
    
    return results

def main():
    input_path = "data/generated/code_samples.json"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Run generate_code.py first.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"Analyzing metrics for {len(samples)} samples...")
    metrics = analyze_batch_metrics(samples)

    output_path = "data/analysis/metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()
