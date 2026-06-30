import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import random

# Configure logging to use the project's standard logging setup if available
try:
    from setup_logging import get_logger, init_logging
    logger = get_logger("stratified_sampling")
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("stratified_sampling")

# Constants
DEFAULT_SAMPLE_SIZE = 150
CAPTIONS_FILE = Path("results/captions.json")
RATES_FILE = Path("results/hallucination_rates.csv")
OUTPUT_FILE = Path("data/sampling_pool.json")

def load_captions(captions_path: Path) -> List[Dict[str, Any]]:
    """Load captions from the JSONL/JSON file produced by T015b."""
    if not captions_path.exists():
        raise FileNotFoundError(f"Captions file not found: {captions_path}")
    
    data = []
    with open(captions_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_hallucination_rates(rates_path: Path) -> Dict[str, float]:
    """
    Load hallucination rates to determine domain weights.
    Returns a dict: {domain: rate}
    """
    if not rates_path.exists():
        raise FileNotFoundError(f"Hallucination rates file not found: {rates_path}")
    
    rates = {}
    with open(rates_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row['domain']
            rate = float(row['rate'])
            rates[domain] = rate
    return rates

def stratified_sample(
    captions: List[Dict[str, Any]], 
    rates: Dict[str, float], 
    total_n: int = DEFAULT_SAMPLE_SIZE
) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling based on domain distribution in the full dataset.
    Ensures representation from all domains present in the data.
    
    Logic:
    1. Group captions by domain.
    2. Calculate proportion of each domain in the total dataset.
    3. Allocate sample count per domain based on proportion (minimum 1 per domain).
    4. Randomly sample from each domain's group.
    """
    # Group by domain
    domain_groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in captions:
        # Expecting 'domain' key in caption metadata
        domain = item.get('domain', 'unknown')
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(item)
    
    if not domain_groups:
        logger.warning("No captions found or no domain metadata available.")
        return []

    total_captions = len(captions)
    sample_allocation = {}
    remaining = total_n
    domains = list(domain_groups.keys())
    num_domains = len(domains)

    # Calculate initial allocation based on proportion
    for domain in domains:
        count = len(domain_groups[domain])
        proportion = count / total_captions
        allocated = int(round(proportion * total_n))
        # Ensure at least 1 if the domain has data, unless total_n is exhausted
        if allocated == 0 and count > 0:
            allocated = 1
        sample_allocation[domain] = allocated
    
    # Adjust for rounding errors to hit exactly total_n
    current_sum = sum(sample_allocation.values())
    
    if current_sum > total_n:
        # Reduce from largest groups
        sorted_domains = sorted(sample_allocation.keys(), key=lambda d: len(domain_groups[d]), reverse=True)
        while current_sum > total_n:
            for d in sorted_domains:
                if sample_allocation[d] > 1:
                    sample_allocation[d] -= 1
                    current_sum -= 1
                    if current_sum == total_n:
                        break
    elif current_sum < total_n:
        # Add to largest groups
        sorted_domains = sorted(sample_allocation.keys(), key=lambda d: len(domain_groups[d]), reverse=True)
        while current_sum < total_n:
            for d in sorted_domains:
                if len(domain_groups[d]) > sample_allocation[d]:
                    sample_allocation[d] += 1
                    current_sum += 1
                    if current_sum == total_n:
                        break

    # Perform sampling
    sampled_items = []
    for domain, count in sample_allocation.items():
        group = domain_groups[domain]
        if count > len(group):
            # Fallback: take all if requested more than available
            count = len(group)
            logger.warning(f"Domain {domain} has only {len(group)} items, taking all.")
        
        # Random sample without replacement
        subset = random.sample(group, count)
        sampled_items.extend(subset)
        
        logger.info(f"Allocated {count} samples from domain {domain} (total available: {len(group)})")

    # Shuffle final list to mix domains
    random.shuffle(sampled_items)
    
    return sampled_items

def save_sampling_pool(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the sampled pool to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2)
    logger.info(f"Saved {len(samples)} samples to {output_path}")

def main() -> int:
    """Main entry point for T027."""
    logger.info("Starting Stratified Sampling (T027)")
    
    # Load inputs
    try:
        captions = load_captions(CAPTIONS_FILE)
        logger.info(f"Loaded {len(captions)} captions from {CAPTIONS_FILE}")
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    try:
        rates = load_hallucination_rates(RATES_FILE)
        logger.info(f"Loaded rates for {len(rates)} domains from {RATES_FILE}")
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    if not captions:
        logger.error("No captions to sample from.")
        return 1

    # Perform sampling
    # Using 150 as the representative sample size per task description (T028a mentions 150)
    sampled = stratified_sample(captions, rates, total_n=DEFAULT_SAMPLE_SIZE)
    
    if not sampled:
        logger.error("Sampling resulted in empty list.")
        return 1

    # Save output
    save_sampling_pool(sampled, OUTPUT_FILE)
    
    logger.info("Stratified sampling completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
