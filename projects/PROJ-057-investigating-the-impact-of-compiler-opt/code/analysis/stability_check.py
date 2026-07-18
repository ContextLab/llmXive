import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class StabilityResult:
    config_id: str
    kernel_type: str
    l2_error: float
    max_diff: float
    status: str  # "stable", "unstable", "nan_detected"
    threshold_exceeded: bool
    raw_log_path: str

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("stability_check")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

def load_raw_logs(log_dir: Path) -> List[Dict[str, Any]]:
    logs = []
    if not log_dir.exists():
        return logs
    for file_path in log_dir.glob("*.jsonl"):
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return logs

def detect_nan_in_tensor(tensor_data: List[float]) -> bool:
    arr = np.array(tensor_data, dtype=np.float32)
    return bool(np.any(np.isnan(arr)))

def calculate_l2_relative_error(reference: List[float], output: List[float]) -> float:
    ref_arr = np.array(reference, dtype=np.float64)
    out_arr = np.array(output, dtype=np.float64)
    if np.linalg.norm(ref_arr) == 0:
        return 0.0 if np.linalg.norm(out_arr) == 0 else float('inf')
    return float(np.linalg.norm(out_arr - ref_arr) / np.linalg.norm(ref_arr))

def calculate_max_absolute_difference(reference: List[float], output: List[float]) -> float:
    ref_arr = np.array(reference, dtype=np.float64)
    out_arr = np.array(output, dtype=np.float64)
    return float(np.max(np.abs(out_arr - ref_arr)))

def process_stability(logs: List[Dict[str, Any]], reference_dir: Path, threshold: float = 1e-5) -> Tuple[List[StabilityResult], List[StabilityResult]]:
    logger = setup_logging()
    stable_results = []
    unstable_results = []

    for log in logs:
        config_id = log.get('config_id', 'unknown')
        kernel_type = log.get('kernel_type', 'unknown')
        output_tensor = log.get('output_tensor', [])
        ref_tensor_path = log.get('reference_tensor_path')
        
        if not ref_tensor_path or not Path(ref_tensor_path).exists():
            logger.warning(f"Reference tensor missing for {config_id}, skipping.")
            continue

        with open(ref_tensor_path, 'rb') as f:
            ref_data = list(struct.unpack('f' * (os.path.getsize(ref_tensor_path) // 4), f.read()))

        if detect_nan_in_tensor(output_tensor):
            result = StabilityResult(
                config_id=config_id,
                kernel_type=kernel_type,
                l2_error=float('inf'),
                max_diff=float('inf'),
                status="nan_detected",
                threshold_exceeded=True,
                raw_log_path=str(log.get('source_file', ''))
            )
            unstable_results.append(result)
            logger.error(f"NaN detected in {config_id} ({kernel_type}). Excluded from analysis.")
            continue

        l2_err = calculate_l2_relative_error(ref_data, output_tensor)
        max_diff = calculate_max_absolute_difference(ref_data, output_tensor)

        is_unstable = l2_err > threshold or max_diff > threshold

        result = StabilityResult(
            config_id=config_id,
            kernel_type=kernel_type,
            l2_error=l2_err,
            max_diff=max_diff,
            status="unstable" if is_unstable else "stable",
            threshold_exceeded=is_unstable,
            raw_log_path=str(log.get('source_file', ''))
        )

        if is_unstable:
            unstable_results.append(result)
            logger.warning(f"Stability failure for {config_id} ({kernel_type}): L2={l2_err:.2e}, MaxDiff={max_diff:.2e}. Excluded from statistical analysis.")
        else:
            stable_results.append(result)
            logger.info(f"Stable run: {config_id} ({kernel_type}).")

    return stable_results, unstable_results

def save_stable_logs(results: List[StabilityResult], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for res in results:
            f.write(json.dumps(asdict(res)) + '\n')

def save_unstable_audit(results: List[StabilityResult], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for res in results:
            f.write(json.dumps(asdict(res)) + '\n')

def main():
    import argparse
    import struct
    
    parser = argparse.ArgumentParser(description="Process stability checks and flag unstable runs.")
    parser.add_argument("--log-dir", type=str, required=True, help="Path to raw logs directory")
    parser.add_argument("--ref-dir", type=str, required=True, help="Path to reference tensors directory")
    parser.add_argument("--output-stable", type=str, default="data/results/stable_metrics.jsonl", help="Output path for stable results")
    parser.add_argument("--output-unstable", type=str, default="data/results/unstable_audit.jsonl", help="Output path for unstable results")
    parser.add_argument("--threshold", type=float, default=1e-5, help="Error threshold for stability")
    args = parser.parse_args()

    logger = setup_logging()
    logs = load_raw_logs(Path(args.log_dir))
    stable, unstable = process_stability(logs, Path(args.ref_dir), args.threshold)
    
    save_stable_logs(stable, Path(args.output_stable))
    save_unstable_audit(unstable, Path(args.output_unstable))
    
    logger.info(f"Processed {len(logs)} logs. Stable: {len(stable)}, Unstable: {len(unstable)}")

if __name__ == "__main__":
    main()
