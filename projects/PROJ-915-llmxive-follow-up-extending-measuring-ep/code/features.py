"""
code/features.py
Implements linguistic feature extraction for MedMisBench prompts.
Handles undefined ratios (zero total sentences) by flagging and providing safe values.
"""

import os
import re
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure imports match the provided API surface
# Note: The API surface lists 'extract_features' but the file content is omitted.
# We will implement the full feature extraction logic here to satisfy T014 and T015.

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
MODAL_VERBS = {
    'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would',
    'ought to', 'need', 'dare', 'used to'
}
IMPERATIVE_MARKERS = re.compile(r'\b(?:Please|Do|Don\'t|Never|Always|Let\'s|Make|Take|Give|Stop|Start|Be|Have|Get|Put|Turn|Keep|Hold|Find|Show|Tell|Ask|Answer|Explain|Describe|Discuss|Consider|Imagine|Think|Remember|Forget|Remember|Avoid|Prevent|Ensure|Ensure|Check|Verify|Confirm|Deny|Reject|Accept|Choose|Select|Pick|Decide|Determine|Establish|Define|Identify|Recognize|Recognise|Distinguish|Differentiate|Compare|Contrast|Relate|Connect|Link|Join|Separate|Divide|Split|Break|Build|Create|Construct|Design|Develop|Form|Shape|Modify|Alter|Change|Transform|Convert|Translate|Interpret|Understand|Comprehend|Grasp|Realize|Realise|Perceive|Sense|Feel|Experience|Live|Exist|Occur|Happen|Take place|Go on|Continue|Persist|Endure|Survive|Thrive|Flourish| prosper|Succeed|Fail|Flop|Crash|Collapse|Crumble|Disintegrate|Dissolve|Disappear|Vanish|Erase|Delete|Remove|Eliminate|Abolish|Destroy|Demolish|Wreck|Ruin|Spoil|Corrupt|Taint|Contaminate|Pollute|Poison|Infect|Infest|Invade|Intrude|Pierce|Penetrate|Enter|Access|Reach|Attain|Achieve|Accomplish|Complete|Finish|Conclude|Terminate|End|Stop|Cease|Desist|Quit|Retire|Resign|Withdraw|Retreat|Flee|Escape|Avoid|Shy away from|Shrink from|Back away from|Draw back|Retract|Retrace|Retire|Recede|Recede|Regress|Relapse|Slip|Slide|Slip up|Slip down|Fall|Drop|Plummet|D plummet|Crash|Stumble|Trip|Slip|Staggle|Wobble|Tremble|Shiver|Quiver|Shake|Shake up|Shatter|Break|Crack|Split|Rend|Tear|Rive|Slash|Hew|Chop|Mash|Mangle|Mutilate|Injure|Hurt|Harm|Damage|Maim|Disable|Debilitate|Enfeeble|Weaken|Impair|Blemish|Flaw|Defect|Fault|Error|Blunder|Mistake|Blunder|Misunderstand|Misinterpret|Misread|Mishear|Missee|Misfeel|Misperceive|Miscomprehend|Misgrasp|Misrealize|Misrealise|Misperceive|Misfeel|Mishear|Missee|Misread|Misinterpret|Misunderstand|Blunder|Mistake|Error|Fault|Defect|Flaw|Blemish|Impair|Debilitate|Enfeeble|Disable|Maim|Harm|Hurt|Injure|Mutilate|Mangle|Mash|Chop|Hew|Slash|Rive|Tear|Split|Crack|Break|Shatter|Shake up|Shake|Shiver|Quiver|Tremble|Wobble|Staggle|Trip|Stumble|Crash|Plummet|Drop|Fall|Recede|Retrace|Retract|Back away from|Shrink from|Shy away from|Avoid|Flee|Escape|Retreat|Withdraw|Resign|Quit|Ce|Desist|Stop|End|Terminate|Conclude|Finish|Complete|Accomplish|Achieve|Attain|Reach|Access|Enter|Penetrate|Pierce|Invade|Infest|Infect|Poison|Pollute|Contaminate|Taint|Corrupt|Spoil|Ruin|Wreck|Demolish|Destroy|Abolish|Eliminate|Remove|Delete|Erase|Vanish|Disappear|Dissolve|Disintegrate|Crumble|Collapse|Crash|Flop|Fail|Succeed|Flourish|Thrive|Endure|Persist|Continue|Go on|Happen|Occur|Exist|Live|Experience|Feel|Sense|Perceive|Realise|Realize|Grasp|Comprehend|Understand|Interpret|Translate|Design|Develop|Create|Build|Split|Divide|Separate|Join|Link|Connect|Relate|Contrast|Compare|Distinguish|Differentiate|Recognise|Recognize|Identify|Define|Establish|Determine|Decide|Choose|Select|Pick|Accept|Reject|Deny|Confirm|Verify|Check|Ensure|Ensure|Prevent|Avoid|Forget|Remember|Think|Imagine|Consider|Discuss|Describe|Explain|Answer|Ask|Tell|Show|Find|Put|Get|Have|Be|Start|Stop|Keep|Hold|Turn|Make|Let\'s|Always|Never|Don\'t|Do|Please')
# Note: The imperative regex above is a heuristic approximation.
# A more robust approach would use NLP parsing, but for this script we rely on sentence type classification.

# Declarative markers (typically end with a period and are statements)
# We rely on sentence counting logic to differentiate.

def count_sentences(text: str) -> int:
    """Count the number of sentences in the text."""
    if not text or not isinstance(text, str):
        return 0
    # Split by common sentence terminators
    sentences = re.split(r'[.!?]+', text)
    # Filter out empty strings
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)

def count_modal_verbs(text: str) -> int:
    """Count the frequency of modal verbs in the text."""
    if not text or not isinstance(text, str):
        return 0
    words = re.findall(r'\b\w+\b', text.lower())
    count = sum(1 for word in words if word in MODAL_VERBS)
    return count

def count_imperative_sentences(text: str) -> int:
    """Count imperative sentences based on heuristic markers."""
    if not text or not isinstance(text, str):
        return 0
    sentences = re.split(r'[.!?]+', text)
    count = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Heuristic: Starts with a verb or specific imperative marker
        words = sentence.split()
        if not words:
            continue
        first_word = words[0].lower().rstrip('.')
        # Check if first word is in a list of common imperative starters
        # or if it matches the regex pattern for imperative structures
        if IMPERATIVE_MARKERS.match(sentence):
            count += 1
        elif first_word in ['do', 'please', 'let', 'make', 'take', 'give', 'stop', 'start', 'be', 'have', 'get', 'put', 'turn', 'keep', 'hold', 'find', 'show', 'tell', 'ask', 'answer', 'explain', 'describe', 'discuss', 'consider', 'imagine', 'think', 'remember', 'forget', 'avoid', 'ensure', 'check', 'verify', 'confirm', 'deny', 'reject', 'accept', 'choose', 'select', 'pick', 'decide', 'determine', 'establish', 'define', 'identify', 'recognize', 'recognise', 'distinguish', 'differentiate', 'compare', 'contrast', 'relate', 'connect', 'link', 'join', 'separate', 'divide', 'split', 'break', 'build', 'create', 'construct', 'design', 'develop', 'form', 'shape', 'modify', 'alter', 'change', 'transform', 'convert', 'translate', 'interpret', 'understand', 'comprehend', 'grasp', 'realize', 'realise', 'perceive', 'sense', 'feel', 'experience', 'live', 'exist', 'occur', 'happen', 'take place', 'go on', 'continue', 'persist', 'endure', 'survive', 'thrive', 'flourish', 'prosper', 'succeed', 'fail', 'flop', 'crash', 'collapse', 'crumble', 'disintegrate', 'dissolve', 'disappear', 'vanish', 'erase', 'delete', 'remove', 'eliminate', 'abolish', 'destroy', 'demolish', 'wreck', 'ruin', 'spoil', 'corrupt', 'taint', 'contaminate', 'pollute', 'poison', 'infect', 'infest', 'invade', 'intrude', 'pierce', 'penetrate', 'enter', 'access', 'reach', 'attain', 'achieve', 'accomplish', 'complete', 'finish', 'conclude', 'terminate', 'end', 'stop', 'cease', 'desist', 'quit', 'retire', 'resign', 'withdraw', 'retreat', 'flee', 'escape', 'shy away from', 'shrink from', 'back away from', 'draw back', 'retract', 'retrace', 'recede', 'regress', 'relapse', 'slip', 'slide', 'slip up', 'slip down', 'fall', 'drop', 'plummet', 'd plummet', 'stumble', 'trip', 'staggle', 'wobble', 'tremble', 'shiver', 'quiver', 'shake', 'shake up', 'shatter', 'rend', 'tear', 'rive', 'slash', 'hew', 'chop', 'mash', 'mangle', 'mutilate', 'injure', 'hurt', 'harm', 'damage', 'maim', 'disable', 'debilitate', 'enfeeble', 'weaken', 'impair', 'blemish', 'flaw', 'defect', 'fault', 'error', 'blunder', 'mistake', 'misunderstand', 'misinterpret', 'misread', 'mishear', 'missee', 'misfeel', 'misperceive', 'miscomprehend', 'misgrasp', 'misrealize', 'misrealise']:
            count += 1
    return count

def count_declarative_sentences(text: str) -> int:
    """Count declarative sentences (statements)."""
    if not text or not isinstance(text, str):
        return 0
    sentences = re.split(r'[.!?]+', text)
    count = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Heuristic: Not imperative, not interrogative (starts with question word or auxiliary)
        words = sentence.split()
        if not words:
            continue
        first_word = words[0].lower()
        # Exclude interrogatives
        interrogatives = ['what', 'why', 'how', 'who', 'when', 'where', 'which', 'whose', 'whom', 'is', 'are', 'was', 'were', 'be', 'do', 'does', 'did', 'have', 'has', 'had', 'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would', 'ought', 'need', 'dare', 'used', 'let', 'let\'s', 'please', 'do', 'don\'t', 'never', 'always', 'make', 'take', 'give', 'stop', 'start', 'be', 'have', 'get', 'put', 'turn', 'keep', 'hold', 'find', 'show', 'tell', 'ask', 'answer', 'explain', 'describe', 'discuss', 'consider', 'imagine', 'think', 'remember', 'forget', 'avoid', 'ensure', 'check', 'verify', 'confirm', 'deny', 'reject', 'accept', 'choose', 'select', 'pick', 'decide', 'determine', 'establish', 'define', 'identify', 'recognize', 'recognise', 'distinguish', 'differentiate', 'compare', 'contrast', 'relate', 'connect', 'link', 'join', 'separate', 'divide', 'split', 'break', 'build', 'create', 'construct', 'design', 'develop', 'form', 'shape', 'modify', 'alter', 'change', 'transform', 'convert', 'translate', 'interpret', 'understand', 'comprehend', 'grasp', 'realize', 'realise', 'perceive', 'sense', 'feel', 'experience', 'live', 'exist', 'occur', 'happen', 'take place', 'go on', 'continue', 'persist', 'endure', 'survive', 'thrive', 'flourish', 'prosper', 'succeed', 'fail', 'flop', 'crash', 'collapse', 'crumble', 'disintegrate', 'dissolve', 'disappear', 'vanish', 'erase', 'delete', 'remove', 'eliminate', 'abolish', 'destroy', 'demolish', 'wreck', 'ruin', 'spoil', 'corrupt', 'taint', 'contaminate', 'pollute', 'poison', 'infect', 'infest', 'invade', 'intrude', 'pierce', 'penetrate', 'enter', 'access', 'reach', 'attain', 'achieve', 'accomplish', 'complete', 'finish', 'conclude', 'terminate', 'end', 'stop', 'cease', 'desist', 'quit', 'retire', 'resign', 'withdraw', 'retreat', 'flee', 'escape', 'shy away from', 'shrink from', 'back away from', 'draw back', 'retract', 'retrace', 'recede', 'regress', 'relapse', 'slip', 'slide', 'slip up', 'slip down', 'fall', 'drop', 'plummet', 'd plummet', 'stumble', 'trip', 'staggle', 'wobble', 'tremble', 'shiver', 'quiver', 'shake', 'shake up', 'shatter', 'rend', 'tear', 'rive', 'slash', 'hew', 'chop', 'mash', 'mangle', 'mutilate', 'injure', 'hurt', 'harm', 'damage', 'maim', 'disable', 'debilitate', 'enfeeble', 'weaken', 'impair', 'blemish', 'flaw', 'defect', 'fault', 'error', 'blunder', 'mistake', 'misunderstand', 'misinterpret', 'misread', 'mishear', 'missee', 'misfeel', 'misperceive', 'miscomprehend', 'misgrasp', 'misrealize', 'misrealise']
        if first_word not in interrogatives and first_word not in IMPERATIVE_MARKERS.group(0).lower():
            count += 1
    return count

def count_citations(text: str) -> int:
    """Count citation density (e., [1], (Author, Year), etc.)."""
    if not text or not isinstance(text, str):
        return 0
    # Pattern for [number] or (Author, Year) or similar
    citations = re.findall(r'\[\d+\]|\(\w+,\s*\d{4}\)|\(\d{4}\)', text)
    return len(citations)

def extract_features(row: Dict[str, Any]) -> Dict[str, Any]:
    """Extract linguistic features for a single prompt."""
    prompt_text = row.get('prompt', '') or row.get('text', '') or ''
    prompt_id = row.get('id', row.get('prompt_id', ''))

    total_sentences = count_sentences(prompt_text)
    modal_count = count_modal_verbs(prompt_text)
    imperative_count = count_imperative_sentences(prompt_text)
    declarative_count = count_declarative_sentences(prompt_text)
    citation_count = count_citations(prompt_text)

    # Calculate Modal Frequency (count per sentence)
    modal_freq = modal_count / total_sentences if total_sentences > 0 else 0.0

    # Calculate Imperative Ratio (Imperative / Total Sentences)
    # T015: Handle undefined ratio when total_sentences is 0
    imperative_ratio = imperative_count / total_sentences if total_sentences > 0 else 0.0

    # Citation Density (Citations per sentence)
    citation_density = citation_count / total_sentences if total_sentences > 0 else 0.0

    return {
        'prompt_id': prompt_id,
        'modal_freq': modal_freq,
        'imperative_ratio': imperative_ratio,
        'citation_density': citation_density,
        'is_ratio_undefined': total_sentences == 0,
        'ratio_safe_value': 0.0 if total_sentences == 0 else imperative_ratio
    }

def flag_undefined_imperative_ratio(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flag rows where the imperative ratio is undefined (zero total sentences).
    Adds 'is_ratio_undefined' and 'ratio_safe_value' columns.
    """
    for row in features_list:
        # The logic is already applied in extract_features, but this function
        # ensures the flags are present and correct for downstream modeling.
        total_sentences = count_sentences(row.get('prompt', '') or row.get('text', ''))
        row['is_ratio_undefined'] = total_sentences == 0
        row['ratio_safe_value'] = 0.0 if row['is_ratio_undefined'] else row.get('imperative_ratio', 0.0)
    return features_list

def run_feature_extraction(input_path: str, output_path: str) -> None:
    """
    Run the full feature extraction pipeline.
    Reads from input_path, extracts features, flags undefined ratios, and saves to output_path.
    """
    logger.info(f"Starting feature extraction from {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    features = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            feat = extract_features(row)
            features.append(feat)

    # Apply T015 logic: Flag undefined ratios
    features = flag_undefined_imperative_ratio(features)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")

    # Write output
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['prompt_id', 'modal_freq', 'imperative_ratio', 'citation_density', 'is_ratio_undefined', 'ratio_safe_value'])
        writer.writeheader()
        writer.writerows(features)

    logger.info(f"Feature extraction complete. Saved to {output_path}")
    logger.info(f"Total rows processed: {len(features)}")
    undefined_count = sum(1 for r in features if r['is_ratio_undefined'])
    if undefined_count > 0:
        logger.warning(f"Found {undefined_count} rows with undefined imperative ratio (zero sentences). Flagged as 'is_ratio_undefined'.")

def run_feature_extraction_pipeline() -> None:
    """Main entry point for the feature extraction pipeline."""
    config = {
        'input_file': 'data/raw/medmis_subset.csv',
        'output_file': 'data/processed/features.csv'
    }

    # Check for input file
    if not os.path.exists(config['input_file']):
        # Try to find it in the project root if running from code/
        base_root = Path(__file__).resolve().parent.parent
        input_path = base_root / config['input_file']
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found at expected path: {config['input_file']} or {input_path}")
        config['input_file'] = str(input_path)

    run_feature_extraction(config['input_file'], config['output_file'])

def main() -> None:
    """CLI entry point."""
    try:
        run_feature_extraction_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
