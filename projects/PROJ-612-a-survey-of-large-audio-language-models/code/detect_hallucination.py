"""
T016: Implement rule-based hallucination detector.

Logic:
1. Read ground truth from JSON files produced by T011b.
2. Read generated captions from results/captions.json.
3. Normalize entities (lowercase, strip).
4. Expand ground-truth entities using WordNet synonyms and fuzzy matching.
5. Flag a sample as hallucinated if a normalized entity in the caption
   is NOT found in the expanded ground-truth set.
6. Output results to results/hallucination_detections.json.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import nltk
from nltk.corpus import wordnet
from fuzzywuzzy import fuzz
from config import load_config, get_dataset_paths, get_sample_limits
from setup_logging import get_logger, init_logging

# Ensure WordNet data is available
try:
    wordnet.synsets("test")
except LookupError:
    nltk.download("wordnet")
    nltk.download("omw-1.4")

# Constants
FUZZY_THRESHOLD = 0.8
LEVENSHTEIN_MAX_DIST = 2
NORMALIZE_WHITESPACE = True

logger = get_logger(__name__)

def normalize_string(s: str) -> str:
    """Normalize string for comparison: lowercase, strip whitespace."""
    if not s:
        return ""
    s = s.lower()
    if NORMALIZE_WHITESPACE:
        s = " ".join(s.split())
    return s.strip()

def get_synonyms(word: str) -> Set[str]:
    """Extract synonyms for a word using WordNet."""
    synonyms = set()
    word_normalized = normalize_string(word)
    if not word_normalized:
        return synonyms

    for syn in wordnet.synsets(word_normalized):
        for lemma in syn.lemmas():
            lemma_name = normalize_string(lemma.name().replace("_", " "))
            if lemma_name:
                synonyms.add(lemma_name)
    return synonyms

def is_fuzzy_match(candidate: str, target: str) -> bool:
    """Check if candidate matches target via fuzzy logic or Levenshtein."""
    if not candidate or not target:
        return False

    c_norm = normalize_string(candidate)
    t_norm = normalize_string(target)

    if c_norm == t_norm:
        return True

    # Levenshtein distance check
    if len(c_norm) <= 10 and len(t_norm) <= 10:
        dist = fuzz.ratio(c_norm, t_norm)
        if dist >= 80:  # 80% similarity
            return True

    # Direct ratio check for longer strings
    if fuzz.ratio(c_norm, t_norm) >= (FUZZY_THRESHOLD * 100):
        return True

    return False

def expand_ground_truth_entities(ground_truth_entities: List[str]) -> Set[str]:
    """
    Expand ground truth entities with synonyms and fuzzy matches.
    Returns a set of all valid normalized strings.
    """
    expanded = set()
    for entity in ground_truth_entities:
        norm_entity = normalize_string(entity)
        if not norm_entity:
            continue

        expanded.add(norm_entity)
        # Add synonyms
        synonyms = get_synonyms(norm_entity)
        expanded.update(synonyms)

        # Note: We cannot fuzzy match against an empty set, so we rely on
        # the fuzzy check during the validation phase against the caption.
        # However, to optimize, we could pre-expand common variations,
        # but for strict correctness based on the prompt, we will check
        # the caption entity against the GT set + synonyms + fuzzy check.

    return expanded

def check_caption_entity_against_gt(caption_entity: str, gt_expanded_set: Set[str], gt_original_list: List[str]) -> bool:
    """
    Check if a caption entity is valid against the ground truth.
    Returns True if valid (found), False if hallucinated.
    """
    norm_cap = normalize_string(caption_entity)
    if not norm_cap:
        return True  # Ignore empty entities

    # 1. Exact match in expanded set (includes synonyms)
    if norm_cap in gt_expanded_set:
        return True

    # 2. Fuzzy match against original ground truth entities
    for gt_entity in gt_original_list:
        if is_fuzzy_match(norm_cap, gt_entity):
            return True

    return False

def load_ground_truth_datasets() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load ground truth data from the JSON files produced by T011b.
    Returns a dict mapping domain -> list of samples.
    """
    dataset_paths = get_dataset_paths()
    samples = {"speech": [], "music": [], "env": []}

    # Map expected paths based on T011b description
    # data/raw/librispeech/dev-clean.json -> speech
    # data/raw/fma_small/metadata.json -> music
    # data/raw/esc50/esc50.json -> env

    paths_map = {
        "speech": dataset_paths.get("librispeech", "data/raw/librispeech/dev-clean.json"),
        "music": dataset_paths.get("fma_small", "data/raw/fma_small/metadata.json"),
        "env": dataset_paths.get("esc50", "data/raw/esc50/esc50.json"),
    }

    for domain, path_str in paths_map.items():
        path = Path(path_str)
        if not path.exists():
            logger.warning(f"Ground truth file not found for {domain}: {path}")
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different JSON structures if necessary
            # Assuming list of dicts with 'audio_id' and 'ground_truth' or similar
            if isinstance(data, list):
                samples[domain].extend(data)
            elif isinstance(data, dict) and "samples" in data:
                samples[domain].extend(data["samples"])
            else:
                logger.warning(f"Unexpected format in {path}")
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")

    return samples

def load_captions() -> List[Dict[str, Any]]:
    """Load generated captions from results/captions.json."""
    captions_path = Path("results/captions.json")
    if not captions_path.exists():
        raise FileNotFoundError(f"Captions file not found: {captions_path}. Run T015b first.")

    with open(captions_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "captions" in data:
        return data["captions"]
    else:
        # Fallback if it's a dict of audio_id -> caption
        return [{"audio_id": k, "caption": v} for k, v in data.items()]

def detect_hallucinations(gt_data: Dict[str, List[Dict]], captions: List[Dict]) -> List[Dict[str, Any]]:
    """
    Perform hallucination detection.
    Returns a list of detection results.
    """
    results = []

    # Pre-process GT data for each domain
    gt_expanded_map = {}
    gt_original_map = {}

    for domain, samples in gt_data.items():
        entities = []
        for sample in samples:
            # Extract ground truth entities
            # Assuming key 'ground_truth', 'label', or 'text'
            gt_text = sample.get("ground_truth") or sample.get("label") or sample.get("text") or ""
            # Simple split by whitespace or comma for entities
            # A more robust parser might be needed depending on exact format
            if isinstance(gt_text, str):
                # Split by common delimiters
                parts = [p.strip() for p in gt_text.replace(",", " ").split() if p.strip()]
                entities.extend(parts)

        gt_expanded_map[domain] = expand_ground_truth_entities(entities)
        gt_original_map[domain] = entities

    for caption_entry in captions:
        audio_id = caption_entry.get("audio_id") or caption_entry.get("id")
        caption_text = caption_entry.get("caption") or caption_entry.get("generated_text", "")
        domain = caption_entry.get("domain", "unknown")

        if not domain or domain not in gt_expanded_map:
            # If domain is unknown or no GT, we might skip or mark as unknown
            # For this task, we assume domain is known from T015b
            if domain not in gt_expanded_map:
                logger.debug(f"No ground truth for domain {domain}, skipping {audio_id}")
                continue

        # Normalize caption text into entities
        # Assuming caption is a string; split into tokens/entities
        caption_entities = [normalize_string(e) for e in caption_text.replace(",", " ").split() if e.strip()]

        hallucinated_entities = []
        is_hallucinated = False

        for entity in caption_entities:
            if not entity:
                continue

            # Check if entity is valid
            if not check_caption_entity_against_gt(entity, gt_expanded_map[domain], gt_original_map[domain]):
                hallucinated_entities.append(entity)
                is_hallucinated = True

        results.append({
            "audio_id": audio_id,
            "domain": domain,
            "caption": caption_text,
            "hallucinated": is_hallucinated,
            "hallucinated_entities": hallucinated_entities,
            "ground_truth_domain": domain
        })

    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save detection results to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved hallucination detection results to {output_path}")

def main():
    """Main entry point for T016."""
    init_logging()
    logger.info("Starting T016: Hallucination Detection")

    try:
        # 1. Load Ground Truth
        logger.info("Loading ground truth datasets...")
        gt_data = load_ground_truth_datasets()
        if not any(gt_data.values()):
            raise RuntimeError("No ground truth data loaded. Ensure T011b has run.")

        # 2. Load Captions
        logger.info("Loading generated captions...")
        captions = load_captions()
        if not captions:
            raise RuntimeError("No captions found. Ensure T015b has run.")

        # 3. Detect Hallucinations
        logger.info(f"Detecting hallucinations for {len(captions)} samples...")
        results = detect_hallucinations(gt_data, captions)

        # 4. Save Results
        output_path = "results/hallucination_detections.json"
        save_results(results, output_path)

        # Log summary
        total = len(results)
        hallucinated_count = sum(1 for r in results if r["hallucinated"])
        logger.info(f"Detection complete. Total: {total}, Hallucinated: {hallucinated_count} ({hallucinated_count/total*100:.2f}%)")

    except Exception as e:
        logger.error(f"Error during hallucination detection: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()