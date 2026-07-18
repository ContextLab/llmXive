"""
Orchestration script for running Baseline and Iterative agents on the curated dataset.
Produces paired_metrics.json for statistical analysis.
"""
import json
import sys
import time
import argparse
import gc
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from sibling modules based on API surface
from config import get_path, get_config_summary, ensure_directories
from utils.memory_manager import MemoryMonitor, clean_up_large_objects
from agent.base import run_baseline_on_dataset
from agent.iterative import run_iterative_on_dataset
from utils.hash_artifacts import compute_sha256, generate_manifest

class ExecutionMonitor:
    """Monitors total execution time and enforces time budget (SC-005)."""
    def __init__(self, max_hours: float = 6.0):
        self.start_time = time.time()
        self.max_seconds = max_hours * 3600
        self.baseline_start: Optional[float] = None
        self.iterative_start: Optional[float] = None

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def check_budget(self, phase: str = "general") -> bool:
        elapsed = self.elapsed()
        if elapsed > self.max_seconds:
            print(f"⚠️  TIME BUDGET EXCEEDED: {phase} phase exceeded {self.max_seconds/3600:.2f}h limit. "
                  f"Elapsed: {elapsed/3600:.2f}h. Aborting remaining tasks.")
            return False
        return True

def load_curated_issues() -> List[Dict[str, Any]]:
    """Loads the curated hard subset and synthetic issues."""
    hard_path = get_path("data/curated/hard_subset.jsonl")
    synthetic_path = get_path("data/curated/synthetic_issues.jsonl")
    
    issues = []
    
    if hard_path.exists():
        with open(hard_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    issues.append(json.loads(line))
        print(f"Loaded {len([i for i in issues if i.get('type') == 'original'])} original hard issues.")
    
    if synthetic_path.exists():
        with open(synthetic_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    issues.append(json.loads(line))
        print(f"Loaded {len([i for i in issues if i.get('type') == 'synthetic'])} synthetic issues.")
    
    if not issues:
        raise FileNotFoundError("No curated issues found in data/curated/. Run curation tasks first.")
    
    return issues

def run_single_issue_baseline(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Runs the baseline agent on a single issue."""
    if not monitor.check_budget("baseline"):
        return None
    
    try:
        result = run_baseline_on_dataset([issue])
        if result and len(result) > 0:
            return result[0]
        return None
    except Exception as e:
        print(f"❌ Baseline failed for {issue.get('issue_id', 'unknown')}: {e}")
        return None

def run_single_issue_iterative(issue: Dict[str, Any], monitor: ExecutionMonitor) -> Optional[Dict[str, Any]]:
    """Runs the iterative agent on a single issue."""
    if not monitor.check_budget("iterative"):
        return None
    
    try:
        result = run_iterative_on_dataset([issue])
        if result and len(result) > 0:
            return result[0]
        return None
    except Exception as e:
        print(f"❌ Iterative failed for {issue.get('issue_id', 'unknown')}: {e}")
        return None

def merge_results(baseline_results: List[Dict], iterative_results: List[Dict]) -> List[Dict]:
    """Merges baseline and iterative results by issue_id for pairing."""
    baseline_map = {r["issue_id"]: r for r in baseline_results if r.get("issue_id")}
    iterative_map = {r["issue_id"]: r for r in iterative_results if r.get("issue_id")}
    
    paired = []
    all_ids = set(baseline_map.keys()) & set(iterative_map.keys())
    
    print(f"Found {len(all_ids)} issues with both baseline and iterative results.")
    
    for issue_id in sorted(all_ids):
        b = baseline_map[issue_id]
        i = iterative_map[issue_id]
        
        pair = {
            "issue_id": issue_id,
            "baseline": {
                "query_count": b.get("query_count", 0),
                "retrieved_context_ids": b.get("retrieved_context_ids", []),
                "coverage_score": b.get("coverage_score", 0.0),
                "success": b.get("success", False)
            },
            "iterative": {
                "turn_count": i.get("turn_count", 0),
                "query_count": i.get("query_count", 0),
                "retrieved_context_ids": i.get("retrieved_context_ids", []),
                "coverage_score": i.get("coverage_score", 0.0),
                "success": i.get("success", False),
                "static_analysis_signals": i.get("static_analysis_signals", [])
            }
        }
        paired.append(pair)
    
    return paired

def main():
    parser = argparse.ArgumentParser(description="Orchestrate Baseline and Iterative agents.")
    parser.add_argument("--max-hours", type=float, default=6.0, help="Max execution time in hours")
    args = parser.parse_args()

    print("🚀 Starting Orchestration Pipeline")
    monitor = ExecutionMonitor(max_hours=args.max_hours)
    
    ensure_directories()
    
    # 1. Load Data
    print("📂 Loading curated issues...")
    issues = load_curated_issues()
    print(f"   Total issues to process: {len(issues)}")
    
    # 2. Run Baseline
    print("🏃 Running Baseline Agent...")
    baseline_results = []
    monitor.baseline_start = time.time()
    for i, issue in enumerate(issues):
        if not monitor.check_budget("baseline"):
            break
        res = run_single_issue_baseline(issue, monitor)
        if res:
            baseline_results.append(res)
        # Periodic GC
        if i % 10 == 0:
            gc.collect()
            clean_up_large_objects()
    print(f"   Baseline complete. {len(baseline_results)} results.")

    # 3. Run Iterative
    print("🔄 Running Iterative Agent...")
    iterative_results = []
    monitor.iterative_start = time.time()
    for i, issue in enumerate(issues):
        if not monitor.check_budget("iterative"):
            break
        res = run_single_issue_iterative(issue, monitor)
        if res:
            iterative_results.append(res)
        if i % 10 == 0:
            gc.collect()
            clean_up_large_objects()
    print(f"   Iterative complete. {len(iterative_results)} results.")

    # 4. Merge and Save
    print("🔗 Merging results...")
    paired_metrics = merge_results(baseline_results, iterative_results)
    
    output_path = get_path("data/results/paired_metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(paired_metrics, f, indent=2)
    
    print(f"✅ Saved paired metrics to {output_path}")
    
    # 5. Hash Artifact
    print("🔒 Hashing output artifact...")
    manifest = generate_manifest([output_path], get_path("data/results/"))
    manifest_path = get_path("data/results/paired_metrics_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"   Manifest saved to {manifest_path}")

    print(f"🏁 Pipeline finished in {monitor.elapsed()/3600:.2f} hours.")
    return 0

if __name__ == "__main__":
    sys.exit(main())