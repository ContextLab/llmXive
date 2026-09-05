import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Import shared config
from config import Config

# Import extraction logic to understand expected fields
from data.extract_geometry import load_scene_data, validate_scene_constraints, extract_constraints

class VLMTraceValidator:
    """
    Validates that the symbolic solver input (constraints.jsonl) contains NO VLM traces.
    
    FR-001: Solver input must be purely geometric/structural.
    FR-002: No semantic embeddings, VLM logits, or natural language reasoning traces 
            from the VLM baseline should exist in the symbolic input stream.
    """
    
    # Known patterns that indicate VLM leakage (LLM/VLM specific artifacts)
    VLM_TRACE_KEYS = {
        "vlm_prediction", "vlm_logit", "vlm_confidence", "vlm_embedding",
        "semantic_trace", "reasoning_chain", "llm_reasoning", "thought_process",
        "vlm_token", "image_embedding", "text_embedding", "attention_weights",
        "vlm_baseline", "baseline_prediction", "neural_score", "probabilities"
    }
    
    # Expected keys in a clean geometric constraint record
    EXPECTED_GEOMETRIC_KEYS = {
        "scene_id", "objects", "constraints", "relationships", "metadata",
        "object_count", "spatial_bounds", "geometry_type", "dimensions"
    }
    
    def __init__(self, config: Config):
        self.config = config
        self.constraints_path = config.DERIVED_DIR / "constraints.jsonl"
        self.results_dir = config.RESULTS_DIR
        self.report_path = self.results_dir / "vlm_purity_validation.json"
        
    def load_constraints(self) -> List[Dict[str, Any]]:
        """Load the extracted constraints file."""
        if not self.constraints_path.exists():
            raise FileNotFoundError(
                f"Constraints file not found: {self.constraints_path}. "
                "Run extract_geometry.py first."
            )
        
        constraints = []
        with open(self.constraints_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    constraints.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON at line {line_num}: {e}")
        return constraints
    
    def check_record_purity(self, record: Dict[str, Any], scene_id: str) -> Tuple[bool, List[str]]:
        """
        Check a single record for VLM traces.
        
        Returns:
            (is_pure, list_of_found_vlm_keys)
        """
        found_traces = []
        
        def scan_dict(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if key matches known VLM trace patterns
                if any(pattern in key.lower() for pattern in self.VLM_TRACE_KEYS):
                    found_traces.append(current_path)
                
                # Recurse into nested dicts
                if isinstance(value, dict):
                    scan_dict(value, current_path)
                # Check lists of dicts
                elif isinstance(value, list):
                    for idx, item in enumerate(value):
                        if isinstance(item, dict):
                            scan_dict(item, f"{current_path}[{idx}]")
        
        scan_dict(record)
        is_pure = len(found_traces) == 0
        return is_pure, found_traces
    
    def validate(self) -> Dict[str, Any]:
        """
        Perform full validation and generate report.
        
        Returns:
            Dictionary with validation results and statistics.
        """
        print(f"Validating VLM purity in {self.constraints_path}...")
        
        constraints = self.load_constraints()
        total_records = len(constraints)
        clean_records = 0
        contaminated_records = 0
        contamination_details = []
        
        for record in constraints:
            scene_id = record.get("scene_id", "unknown")
            is_pure, found_traces = self.check_record_purity(record, scene_id)
            
            if is_pure:
                clean_records += 1
            else:
                contaminated_records += 1
                contamination_details.append({
                    "scene_id": scene_id,
                    "found_keys": found_traces
                })
        
        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report
        report = {
            "validation_status": "passed" if contaminated_records == 0 else "failed",
            "total_records": total_records,
            "clean_records": clean_records,
            "contaminated_records": contaminated_records,
            "purity_percentage": (clean_records / total_records * 100) if total_records > 0 else 0.0,
            "contamination_samples": contamination_details[:10],  # Limit to first 10 for brevity
            "checked_at": str(Path(__file__).parent.parent.name) + " validation",
            "description": "Validates that solver input contains no VLM traces (FR-001, FR-002)"
        }
        
        # Save report
        with open(self.report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    """Entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Validate that solver input contains no VLM traces."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to config file (default: code/config.py)"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = Config()
    
    try:
        validator = VLMTraceValidator(config)
        report = validator.validate()
        
        status = "✅ PASSED" if report["validation_status"] == "passed" else "❌ FAILED"
        print(f"\nValidation {status}:")
        print(f"  Total records: {report['total_records']}")
        print(f"  Clean records: {report['clean_records']}")
        print(f"  Contaminated records: {report['contaminated_records']}")
        print(f"  Purity: {report['purity_percentage']:.2f}%")
        
        if report["contaminated_records"] > 0:
            print(f"\n⚠️  Contamination detected! See report: {validator.report_path}")
            sys.exit(1)
        else:
            print("\n✅ No VLM traces found. Solver input is pure.")
            sys.exit(0)
            
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
