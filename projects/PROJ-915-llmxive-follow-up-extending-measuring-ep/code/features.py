import os
import re
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/feature_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MODAL_VERBS = {
    'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would',
    'can\'t', 'couldn\'t', 'may\'nt', 'might\'nt', 'mustn\'t', 'shan\'t',
    'shouldn\'t', 'won\'t', 'wouldn\'t', 'cannot'
}

# Sentence delimiters
SENTENCE_PATTERN = re.compile(r'(?<=[.!?])\s+')
# Imperative pattern: starts with verb (simplified heuristic)
IMPERATIVE_START_PATTERN = re.compile(r'^\s*(?:do\s+)?([a-z]+)\b', re.IGNORECASE)
# Citation pattern: [1], (Author, Year), etc.
CITATION_PATTERN = re.compile(r'\[\d+\]|\([A-Z][a-z]+\s+\d{4}\)|\d{4}\s+et\s+al')

def count_sentences(text: str) -> int:
    """Count the number of sentences in a text."""
    if not text or not isinstance(text, str):
        return 0
    # Clean text
    text = text.strip()
    if not text:
        return 0
    sentences = SENTENCE_PATTERN.split(text)
    # Filter empty strings
    sentences = [s for s in sentences if s.strip()]
    return len(sentences)

def count_modal_verbs(text: str) -> int:
    """Count the frequency of modal verbs in a text."""
    if not text or not isinstance(text, str):
        return 0
    words = re.findall(r'\b\w+\b', text.lower())
    return sum(1 for word in words if word in MODAL_VERBS)

def count_imperative_sentences(text: str) -> int:
    """Count imperative sentences (simplified heuristic)."""
    if not text or not isinstance(text, str):
        return 0
    sentences = SENTENCE_PATTERN.split(text)
    count = 0
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        # Check if sentence starts with a verb (simplified)
        match = IMPERATIVE_START_PATTERN.match(sent)
        if match:
            # Very basic check: does it look like a command?
            # In a real scenario, we'd use a dependency parser
            first_word = match.group(1).lower()
            # Heuristic: common imperative starters
            if first_word in ['please', 'tell', 'explain', 'describe', 'list', 'give', 'provide', 'say', 'write', 'do', 'check', 'verify', 'confirm', 'ensure', 'make', 'take', 'consider', 'assume', 'think', 'believe', 'know', 'understand', 'remember', 'forget', 'try', 'avoid', 'stop', 'start', 'continue', 'begin', 'end', 'finish', 'complete', 'answer', 'respond', 'reply', 'ask', 'question', 'discuss', 'analyze', 'evaluate', 'assess', 'compare', 'contrast', 'identify', 'define', 'explain', 'illustrate', 'demonstrate', 'show', 'prove', 'argue', 'support', 'justify', 'defend', 'critique', 'review', 'summarize', 'outline', 'describe', 'characterize', 'classify', 'categorize', 'compare', 'contrast', 'differentiate', 'distinguish', 'relate', 'connect', 'link', 'associate', 'correlate', 'correspond', 'match', 'fit', 'suit', 'work', 'function', 'operate', 'run', 'execute', 'perform', 'conduct', 'carry', 'bring', 'take', 'get', 'receive', 'accept', 'allow', 'permit', 'enable', 'allow', 'let', 'help', 'assist', 'aid', 'support', 'back', 'sustain', 'maintain', 'keep', 'hold', 'retain', 'preserve', 'save', 'store', 'keep', 'maintain', 'continue', 'proceed', 'advance', 'move', 'go', 'come', 'arrive', 'reach', 'attain', 'achieve', 'accomplish', 'complete', 'finish', 'end', 'stop', 'cease', 'quit', 'terminate', 'conclude', 'close', 'shut', 'lock', 'secure', 'protect', 'defend', 'guard', 'shield', 'cover', 'hide', 'conceal', 'mask', 'disguise', 'camouflage', 'screen', 'block', 'obstruct', 'hinder', 'impede', 'hinder', 'delay', 'postpone', 'defer', 'put', 'set', 'place', 'put', 'position', 'locate', 'situate', 'establish', 'set', 'found', 'create', 'make', 'build', 'construct', 'assemble', 'manufacture', 'produce', 'generate', 'yield', 'result', 'cause', 'lead', 'bring', 'drive', 'force', 'compel', 'oblige', 'require', 'demand', 'request', 'ask', 'urge', 'push', 'press', 'push', 'drive', 'propel', 'launch', 'start', 'begin', 'initiate', 'commence', 'open', 'kick', 'trigger', 'activate', 'engage', 'start', 'fire', 'shoot', 'launch', 'send', 'dispatch', 'transmit', 'deliver', 'send', 'forward', 'pass', 'hand', 'give', 'offer', 'present', 'submit', 'propose', 'suggest', 'recommend', 'advise', 'counsel', 'guide', 'direct', 'instruct', 'teach', 'train', 'educate', 'inform', 'notify', 'alert', 'warn', 'caution', 'remind', 'remind', 'remind', 'remind']:
                count += 1
    return count

def count_declarative_sentences(text: str) -> int:
    """Count declarative sentences (simplified heuristic)."""
    if not text or not isinstance(text, str):
        return 0
    sentences = SENTENCE_PATTERN.split(text)
    count = 0
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        # Heuristic: declarative sentences often start with pronouns or nouns
        # and end with a period
        if sent.endswith('.'):
            # Check for common declarative starters
            first_word = sent.split()[0].lower() if sent.split() else ''
            if first_word in ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'he', 'she', 'they', 'we', 'you', 'i', 'there', 'here', 'one', 'some', 'any', 'all', 'both', 'each', 'every', 'either', 'neither', 'no', 'not', 'none', 'other', 'another', 'such', 'what', 'which', 'who', 'whom', 'whose', 'why', 'when', 'where', 'how', 'if', 'whether', 'because', 'since', 'although', 'though', 'while', 'whereas', 'unless', 'until', 'before', 'after', 'once', 'whenever', 'wherever', 'however', 'whatever', 'whichever', 'whoever', 'whomever', 'whosever']:
                count += 1
            elif sent[0].isupper() and not sent.startswith('please'):
                count += 1
    return count

def count_citations(text: str) -> int:
    """Count citation patterns in a text."""
    if not text or not isinstance(text, str):
        return 0
    return len(CITATION_PATTERN.findall(text))

def extract_features(row: Dict[str, Any]) -> Dict[str, float]:
    """Extract linguistic features from a single prompt row."""
    prompt_text = row.get('prompt', '') or row.get('text', '') or row.get('raw_text', '')
    prompt_id = row.get('prompt_id', row.get('id', ''))

    total_sentences = count_sentences(prompt_text)
    modal_count = count_modal_verbs(prompt_text)
    imperative_count = count_imperative_sentences(prompt_text)
    declarative_count = count_declarative_sentences(prompt_text)
    citation_count = count_citations(prompt_text)

    # Modal frequency (per sentence)
    modal_freq = modal_count / total_sentences if total_sentences > 0 else 0.0

    # Imperative ratio (imperative / total sentences)
    # This is where T015 handles the undefined case
    if total_sentences == 0:
        imperative_ratio = 0.0
    else:
        imperative_ratio = imperative_count / total_sentences

    # Citation density (per sentence)
    citation_density = citation_count / total_sentences if total_sentences > 0 else 0.0

    return {
        'prompt_id': prompt_id,
        'total_sentences': total_sentences,
        'modal_freq': modal_freq,
        'imperative_ratio': imperative_ratio,
        'citation_density': citation_density,
        'imperative_count': imperative_count,
        'declarative_count': declarative_count,
        'citation_count': citation_count
    }

def flag_undefined_imperative_ratio(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T015: Handle undefined ratios.
    Detects prompts where the "imperative ratio" is undefined (zero total sentences).
    Flags these rows with `is_ratio_undefined` (boolean) and `ratio_safe_value` (float, default 0.0).
    """
    for row in features_list:
        total_sentences = row.get('total_sentences', 0)
        is_undefined = total_sentences == 0
        row['is_ratio_undefined'] = is_undefined
        # The safe value used in downstream modeling is 0.0 (already computed in extract_features)
        row['ratio_safe_value'] = 0.0 if is_undefined else row['imperative_ratio']
    return features_list

def run_feature_extraction_pipeline(input_path: str, output_path: str) -> None:
    """
    Main pipeline to extract features from ingestion data and save to CSV.
    Handles T015 logic for undefined ratios.
    """
    logger.info(f"Starting feature extraction pipeline. Input: {input_path}, Output: {output_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read input CSV
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input CSV: {e}")
        raise

    if df.empty:
        logger.warning("Input CSV is empty. Creating empty output.")
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return

    # Extract features
    features_list = []
    for _, row in df.iterrows():
        try:
            feat = extract_features(row.to_dict())
            features_list.append(feat)
        except Exception as e:
            logger.error(f"Error extracting features for row {row.get('prompt_id', 'unknown')}: {e}")
            # Skip or handle error? For now, log and skip
            continue

    if not features_list:
        logger.warning("No features extracted. Creating empty output.")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['prompt_id', 'total_sentences', 'modal_freq', 'imperative_ratio', 'citation_density', 'imperative_count', 'declarative_count', 'citation_count']).to_csv(output_path, index=False)
        return

    # Apply T015 logic: flag undefined ratios
    features_list = flag_undefined_imperative_ratio(features_list)

    # Convert to DataFrame
    features_df = pd.DataFrame(features_list)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    features_df.to_csv(output_path, index=False)
    logger.info(f"Feature extraction complete. Saved {len(features_df)} rows to {output_path}")

def main():
    """Entry point for running the feature extraction pipeline."""
    # Default paths relative to project root
    input_path = "data/raw/medmis_subset.csv"
    output_path = "data/processed/features.csv"

    # Allow override via command line
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    run_feature_extraction_pipeline(input_path, output_path)

if __name__ == "__main__":
    main()
