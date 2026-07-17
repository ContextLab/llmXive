import re
from typing import List, Union
import sacrebleu

def calculate_bleu(references: List[str], candidate: str) -> float:
    """Calculate BLEU score between references and candidate."""
    return sacrebleu.sentence_bleu(candidate, references).score

def parse_latency_to_ms(latency_str: str) -> int:
    """Parse latency string to milliseconds."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*(ms|s|min)', latency_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid latency format: {latency_str}")
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == 's':
        return int(value * 1000)
    elif unit == 'min':
        return int(value * 60 * 1000)
    return int(value)

def calculate_latency_stats(latencies: List[int]) -> dict:
    """Calculate statistics for latency values."""
    if not latencies:
        return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0}
    return {
        "mean": sum(latencies) / len(latencies),
        "median": sorted(latencies)[len(latencies) // 2],
        "std": (sum((x - sum(latencies)/len(latencies))**2 for x in latencies) / len(latencies)) ** 0.5,
        "min": min(latencies),
        "max": max(latencies)
    }
