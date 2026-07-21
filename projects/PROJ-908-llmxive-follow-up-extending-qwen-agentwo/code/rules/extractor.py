"""
Rule Extractor Module for llmXive Follow-up Project.

This module implements First-Order Logic (FOL) and Inductive Logic Programming (ILP)
techniques to derive explicit logical rules from LLM Chain-of-Thought (CoT) traces.
It uses the `prolog` library for logical representation and induction logic.

The extractor processes CoT traces to identify patterns in state transitions,
spatial reasoning, and causal relationships, outputting a set of hypothesized rules.
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Iterator
from collections import Counter

# Attempt to import prolog for FOL representation
try:
    from prolog import Prolog
    PROLOG_AVAILABLE = True
except ImportError:
    PROLOG_AVAILABLE = False
    logging.warning("prolog library not installed. ILP induction will be simulated with heuristic pattern matching.")

from utils.loaders import load_cot_traces

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedRule:
    """Represents a single extracted logical rule."""
    rule_id: str
    head: str
    body: List[str]
    confidence: float
    support_count: int
    pattern_type: str  # e.g., "spatial", "temporal", "causal", "conditional"
    source_trace_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RuleExtractor:
    """
    Extracts logical rules from CoT traces using FOL/ILP techniques.

    This class implements a simplified ILP induction strategy:
    1. Parse CoT traces to identify state transitions and logical connectives.
    2. Generalize specific instances into abstract rules (variable substitution).
    3. Validate rules against frequency thresholds (support).
    4. Assign confidence based on consistency across traces.
    """

    def __init__(self, min_support: int = 2, min_confidence: float = 0.6):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.rule_counter = 0
        self.pattern_templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for common logical structures in CoT."""
        return {
            "spatial": re.compile(
                r"(?:move|go|navigate|travel|position|located) to (?:the )?(\w+)",
                re.IGNORECASE
            ),
            "causal": re.compile(
                r"(?:because|since|due to|as a result of|therefore) (.*?)(?:\.|,|;|$)",
                re.IGNORECASE
            ),
            "conditional": re.compile(
                r"(?:if|when|provided that|in case) (.*?)(?:,|:|then|do)",
                re.IGNORECASE
            ),
            "temporal": re.compile(
                r"(?:before|after|while|during|once|until) (.*?)(?:,|:|then|do)",
                re.IGNORECASE
            ),
            "state_change": re.compile(
                r"(?:state|status|condition|inventory) (?:changes?|becomes?|is set to) (.*?)(?:\.|,|;|$)",
                re.IGNORECASE
            )
        }

    def _parse_trace_to_facts(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses a single CoT trace into a list of logical facts.
        Converts natural language steps into structured representations.
        """
        facts = []
        trace_id = trace.get("id", "unknown")
        steps = trace.get("steps", [])

        for step_idx, step in enumerate(steps):
            text = step.get("thought", "") or step.get("action", "")
            if not text:
                continue

            # Extract potential facts based on patterns
            for pattern_type, pattern in self.pattern_templates.items():
                matches = pattern.findall(text)
                for match in matches:
                    facts.append({
                        "trace_id": trace_id,
                        "step_idx": step_idx,
                        "type": pattern_type,
                        "content": match.strip(),
                        "raw_text": text
                    })

            # Generic state transition extraction
            if "action" in step and "result" in step:
                facts.append({
                    "trace_id": trace_id,
                    "step_idx": step_idx,
                    "type": "state_transition",
                    "content": f"{step['action']} -> {step['result']}",
                    "raw_text": text
                })

        return facts

    def _generalize_facts(self, facts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups facts by pattern type and content to identify recurring structures.
        Performs simple variable abstraction (e.g., 'room_A' -> 'Location').
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for fact in facts:
            key = f"{fact['type']}_{fact['content']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(fact)

        return grouped

    def _abstract_content(self, content: str) -> str:
        """
        Abstracts specific tokens (like room names, item IDs) into variables.
        Example: 'move to room_A' -> 'move to Variable_Location'
        """
        # Replace alphanumeric identifiers with placeholders
        abstracted = re.sub(r'\b[A-Z][a-z]+_[A-Z0-9]+\b', 'Variable_Location', content)
        abstracted = re.sub(r'\bitem_\w+\b', 'Variable_Item', abstracted)
        abstracted = re.sub(r'\bagent_\w+\b', 'Variable_Agent', abstracted)
        return abstracted

    def _construct_rule_body(self, content: str) -> List[str]:
        """
        Constructs a logical body from the abstracted content.
        Returns a list of logical literals.
        """
        literals = []
        # Simple heuristic: split by common logical connectors
        parts = re.split(r'\s+(and|or|but|while)\s+', content, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if part.lower() in ['and', 'or', 'but', 'while']:
                continue
            if part:
                literals.append(f"condition({part})")
        return literals if literals else [f"condition({content})"]

    def _construct_rule_head(self, pattern_type: str, content: str) -> str:
        """
        Constructs a logical head based on the pattern type.
        """
        abstracted = self._abstract_content(content)
        if pattern_type == "spatial":
            return f"at(Agent, {abstracted})"
        elif pattern_type == "causal":
            return f"effect(Effect) :- cause({abstracted})"
        elif pattern_type == "conditional":
            return f"action(Action) :- condition({abstracted})"
        elif pattern_type == "temporal":
            return f"next_state(State) :- current_state(Current), {abstracted}"
        else:
            return f"state_change({abstracted})"

    def _calculate_confidence(self, rule_facts: List[Dict[str, Any]]) -> float:
        """
        Calculates confidence based on consistency of the pattern across traces.
        High confidence if the pattern appears in many different traces.
        """
        if not rule_facts:
            return 0.0
        unique_traces = len(set(f["trace_id"] for f in rule_facts))
        total_facts = len(rule_facts)
        # Confidence is ratio of unique traces to total occurrences (penalizes repetition in single trace)
        return min(1.0, unique_traces / max(1, total_facts))

    def _generate_prolog_program(self, rules: List[ExtractedRule]) -> str:
        """
        Generates a Prolog program string from the extracted rules.
        """
        if not PROLOG_AVAILABLE:
            logger.warning("Prolog library not available, skipping Prolog generation.")
            return ""

        program_lines = ["% Extracted Rules from llmXive CoT Traces", "% Generated by RuleExtractor"]
        for rule in rules:
            body_str = " , ".join(rule.body)
            if body_str:
                clause = f"{rule.head} :- {body_str}."
            else:
                clause = f"{rule.head}."
            program_lines.append(clause)
            program_lines.append(f"% Confidence: {rule.confidence:.2f}, Support: {rule.support_count}")

        return "\n".join(program_lines)

    def extract_rules(self, traces: List[Dict[str, Any]]) -> List[ExtractedRule]:
        """
        Main entry point for rule extraction.
        Processes all traces and returns a list of ExtractedRule objects.
        """
        logger.info(f"Starting rule extraction on {len(traces)} traces.")

        all_facts = []
        for trace in traces:
            facts = self._parse_trace_to_facts(trace)
            all_facts.extend(facts)

        logger.info(f"Extracted {len(all_facts)} candidate facts.")

        grouped_facts = self._generalize_facts(all_facts)
        rules = []

        for key, fact_list in grouped_facts.items():
            if len(fact_list) < self.min_support:
                continue

            # Extract pattern type and content from key
            parts = key.split("_", 1)
            if len(parts) == 2:
                pattern_type = parts[0]
                content = parts[1]
            else:
                pattern_type = "generic"
                content = key

            head = self._construct_rule_head(pattern_type, content)
            body = self._construct_rule_body(content)
            confidence = self._calculate_confidence(fact_list)

            if confidence < self.min_confidence:
                continue

            self.rule_counter += 1
            rule = ExtractedRule(
                rule_id=f"RULE_{self.rule_counter:04d}",
                head=head,
                body=body,
                confidence=confidence,
                support_count=len(fact_list),
                pattern_type=pattern_type,
                source_trace_ids=list(set(f["trace_id"] for f in fact_list))
            )
            rules.append(rule)

        # Sort rules by support count (descending)
        rules.sort(key=lambda r: r.support_count, reverse=True)
        logger.info(f"Extracted {len(rules)} valid rules.")
        return rules

def main(
    input_path: str = "data/raw/cot_traces.json",
    output_path: str = "data/processed/extracted_rules.json",
    min_support: int = 2,
    min_confidence: float = 0.6
) -> None:
    """
    Main function to execute the rule extraction pipeline.

    Args:
        input_path: Path to the input CoT traces JSON file.
        output_path: Path to save the extracted rules JSON file.
        min_support: Minimum number of occurrences for a rule to be considered.
        min_confidence: Minimum confidence score for a rule to be accepted.
    """
    logger.info(f"Loading CoT traces from {input_path}")
    try:
        traces = load_cot_traces(input_path)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load traces: {e}")
        raise

    extractor = RuleExtractor(min_support=min_support, min_confidence=min_confidence)
    rules = extractor.extract_rules(traces)

    # Prepare output data
    output_data = {
        "metadata": {
            "total_traces_processed": len(traces),
            "total_rules_extracted": len(rules),
            "min_support": min_support,
            "min_confidence": min_confidence
        },
        "rules": [r.to_dict() for r in rules]
    }

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Extracted rules saved to {output_path}")

    # Optional: Generate Prolog program if library is available
    if PROLOG_AVAILABLE:
        prolog_code = extractor._generate_prolog_program(rules)
        prolog_path = str(output_file.parent / "extracted_rules.pl")
        with open(prolog_path, 'w', encoding='utf-8') as f:
            f.write(prolog_code)
        logger.info(f"Prolog program saved to {prolog_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract logical rules from CoT traces.")
    parser.add_argument("--input", type=str, default="data/raw/cot_traces.json", help="Input traces file")
    parser.add_argument("--output", type=str, default="data/processed/extracted_rules.json", help="Output rules file")
    parser.add_argument("--min-support", type=int, default=2, help="Minimum support count")
    parser.add_argument("--min-confidence", type=float, default=0.6, help="Minimum confidence score")

    args = parser.parse_args()

    main(
        input_path=args.input,
        output_path=args.output,
        min_support=args.min_support,
        min_confidence=args.min_confidence
    )
