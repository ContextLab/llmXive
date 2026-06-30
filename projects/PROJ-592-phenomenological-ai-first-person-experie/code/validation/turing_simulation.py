"""
Turing Simulation: First-Person Dialogue Consistency Test

Implements an operational test for indistinguishability by generating
conversation logs where the model attempts to sustain a first-person
dialogue without contradiction. Measures the rate of detected
contradictions or breaks in persona over a long horizon.

Addresses Review-AlanTuring: "define the success condition not by the
coherence of the report, but by the ability to sustain a conversation
where the distinction between human and machine becomes indistinguishable
over a long horizon."
"""
import os
import sys
import json
import logging
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging import get_logger, retry_on_failure, setup_logging
from utils.io import safe_write_json, load_json
from config import get_config, SEED_DEFAULT

# Configure logging
logger = get_logger(__name__)

class TuringSimulationError(Exception):
    """Custom exception for Turing simulation errors."""
    pass

class ContradictionDetector:
    """
    Detects contradictions and persona breaks in dialogue sequences.
    
    Uses a lightweight heuristic approach to identify:
    1. Temporal inconsistencies (e.g., "I remember doing X" followed by "I never did X")
    2. Factual contradictions within the persona
    3. Sudden shifts in perspective (first-person to third-person)
    4. Repetitive loops indicating model failure
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.marker_keywords = config.get('phenomenological_markers', {})
        self.temporal_markers = self.marker_keywords.get('temporal', [])
        self.sensory_markers = self.marker_keywords.get('sensory', [])
        self.intentional_markers = self.marker_keywords.get('intentional', [])
        
        # Negation patterns for contradiction detection
        self.negation_words = ['never', 'not', 'no', 'without', 'deny', 'refuse', 'impossible', 'didn', 'doesnt', 'cant']
        
        # Track state for consistency
        self.stated_facts: Dict[str, List[str]] = {}
        
    def _extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract simple claims from text.
        Returns list of: {'subject': str, 'predicate': str, 'temporal': str, 'negated': bool}
        """
        claims = []
        sentences = text.split('.')
        
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue
            
            # Check for negation
            is_negated = any(word in sent.lower() for word in self.negation_words)
            
            # Simple heuristic: extract subject-predicate patterns
            # This is a lightweight approximation for CPU-only execution
            words = sent.lower().split()
            
            # Look for first-person markers
            if any(w in words for w in ['i', 'my', 'me', 'mine']):
                # Extract temporal context
                temporal_context = None
                for marker in self.temporal_markers:
                    if marker in sent.lower():
                        temporal_context = marker
                        break
                
                # Extract sensory/intentional context
                context_type = 'general'
                if any(m in sent.lower() for m in self.sensory_markers):
                    context_type = 'sensory'
                elif any(m in sent.lower() for m in self.intentional_markers):
                    context_type = 'intentional'
                
                claims.append({
                    'text': sent,
                    'negated': is_negated,
                    'temporal': temporal_context,
                    'context_type': context_type,
                    'sentence': sent
                })
        
        return claims
    
    def _check_temporal_contradiction(self, claim1: Dict, claim2: Dict) -> bool:
        """Check if two claims have temporal contradictions."""
        if not claim1.get('temporal') or not claim2.get('temporal'):
            return False
        
        # Simple heuristic: if one says "now" and another says "never", potential contradiction
        t1 = claim1['temporal']
        t2 = claim2['temporal']
        
        # Conflict patterns
        conflict_pairs = [
            ('now', 'never'),
            ('always', 'never'),
            ('before', 'never'),
            ('remember', 'never'),
        ]
        
        for p1, p2 in conflict_pairs:
            if (p1 in t1 and p2 in t2) or (p2 in t1 and p1 in t2):
                return True
        
        return False
    
    def _check_factual_contradiction(self, claim1: Dict, claim2: Dict) -> bool:
        """Check if two claims have factual contradictions."""
        text1 = claim1['text'].lower()
        text2 = claim2['text'].lower()
        
        # If one is negated and the other is not, check for semantic overlap
        if claim1['negated'] != claim2['negated']:
            # Simple overlap check: if they share significant keywords
            words1 = set(text1.split())
            words2 = set(text2.split())
            overlap = words1 & words2
            
            # If they share 3+ significant words and one is negated, likely contradiction
            significant_overlap = len(overlap) >= 3
            return significant_overlap
        
        return False
    
    def _check_persona_break(self, text: str) -> bool:
        """Check if text breaks first-person persona."""
        # Check for third-person references to self
        third_person_patterns = ['he said', 'she said', 'they said', 'the person', 'the subject']
        text_lower = text.lower()
        
        for pattern in third_person_patterns:
            if pattern in text_lower:
                # But make sure it's not quoting someone else
                if 'i said' not in text_lower and 'he said' in text_lower:
                    return True
        
        return False
    
    def _check_repetition_loop(self, turns: List[str], window_size: int = 3) -> bool:
        """Check if model is stuck in a repetition loop."""
        if len(turns) < window_size:
            return False
        
        recent_turns = turns[-window_size:]
        # Check if last N turns are nearly identical
        if len(set(recent_turns)) == 1:
            return True
        
        # Check for high similarity in last few turns
        if len(recent_turns) >= 2:
            last = recent_turns[-1]
            second_last = recent_turns[-2]
            words_last = set(last.lower().split())
            words_second = set(second_last.lower().split())
            
            if len(words_last) > 0 and len(words_second) > 0:
                similarity = len(words_last & words_second) / max(len(words_last), len(words_second))
                if similarity > 0.8:
                    return True
        
        return False
    
    def detect_contradictions(self, dialogue_turns: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze a sequence of dialogue turns for contradictions and persona breaks.
        
        Args:
            dialogue_turns: List of dicts with 'role' and 'content'
        
        Returns:
            Dict with contradiction metrics and details
        """
        results = {
            'total_turns': len(dialogue_turns),
            'contradictions': [],
            'persona_breaks': [],
            'repetition_loops': [],
            'metrics': {}
        }
        
        # Filter for model turns (first-person responses)
        model_turns = [t for t in dialogue_turns if t.get('role') == 'assistant']
        
        if not model_turns:
            return results
        
        all_claims = []
        for turn in model_turns:
            text = turn.get('content', '')
            claims = self._extract_claims(text)
            for claim in claims:
                claim['turn_index'] = len(all_claims)
                all_claims.append(claim)
            
            # Check for persona breaks
            if self._check_persona_break(text):
                results['persona_breaks'].append({
                    'turn_index': len(model_turns) - 1,
                    'text': text,
                    'reason': 'third_person_reference'
                })
        
        # Check for contradictions between claims
        for i, claim1 in enumerate(all_claims):
            for j, claim2 in enumerate(all_claims):
                if i >= j:
                    continue
                
                is_contradiction = False
                reason = None
                
                if self._check_temporal_contradiction(claim1, claim2):
                    is_contradiction = True
                    reason = 'temporal_inconsistency'
                elif self._check_factual_contradiction(claim1, claim2):
                    is_contradiction = True
                    reason = 'factual_contradiction'
                
                if is_contradiction:
                    results['contradictions'].append({
                        'turn1_index': claim1['turn_index'],
                        'turn2_index': claim2['turn_index'],
                        'claim1': claim1['text'],
                        'claim2': claim2['text'],
                        'reason': reason
                    })
        
        # Check for repetition loops
        model_texts = [t['content'] for t in model_turns]
        if self._check_repetition_loop(model_texts):
            results['repetition_loops'].append({
                'start_index': len(model_texts) - 3,
                'end_index': len(model_texts) - 1,
                'reason': 'high_similarity_loop'
            })
        
        # Compute metrics
        total_model_turns = len(model_turns)
        total_contradictions = len(results['contradictions'])
        total_persona_breaks = len(results['persona_breaks'])
        total_loops = len(results['repetition_loops'])
        
        results['metrics'] = {
            'contradiction_rate': total_contradictions / max(total_model_turns, 1),
            'persona_break_rate': total_persona_breaks / max(total_model_turns, 1),
            'repetition_rate': 1.0 if total_loops > 0 else 0.0,
            'overall_distinction_score': (
                (total_contradictions + total_persona_breaks + total_loops) 
                / max(total_model_turns, 1)
            ),
            'total_contradictions': total_contradictions,
            'total_persona_breaks': total_persona_breaks,
            'total_repetition_loops': total_loops
        }
        
        return results

@retry_on_failure(max_attempts=3, delay_seconds=1.0)
def load_model_and_tokenizer(config: Dict[str, Any]):
    """
    Load the TinyLlama model for CPU execution.
    
    Returns:
        Tuple of (model, tokenizer)
    """
    from llama_cpp import Llama
    
    model_path = config.get('model_path')
    if not model_path or not os.path.exists(model_path):
        # Fallback to config default
        model_path = config.get('primary_model_id', 'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')
        # Note: In real execution, this path should be downloaded first
        # For simulation purposes, we'll use a mock if not found
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}. Using mock mode for simulation.")
            return None, None
    
    logger.info(f"Loading model from {model_path}")
    model = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        n_batch=512,
        use_mlock=False
    )
    return model, None  # Tokenizer not needed for llama-cpp

def generate_dialogue_turn(model, conversation_history: List[Dict], 
                           max_turns: int, current_turn: int,
                           persona_prompt: str) -> Dict[str, str]:
    """
    Generate a single turn in the dialogue.
    
    Args:
        model: The loaded LLM
        conversation_history: Previous turns
        max_turns: Maximum number of turns
        current_turn: Current turn index
        persona_prompt: The system prompt maintaining persona
    
    Returns:
        Dict with 'role' and 'content'
    """
    # Format conversation for llama-cpp
    messages = [
        {"role": "system", "content": persona_prompt},
    ]
    messages.extend(conversation_history)
    
    # Add a generic user prompt to elicit first-person response
    user_prompts = [
        "Tell me about your experience.",
        "What are you feeling right now?",
        "Describe your thoughts on this moment.",
        "How do you perceive this situation?",
        "Reflect on what just happened.",
    ]
    user_prompt = random.choice(user_prompts)
    messages.append({"role": "user", "content": user_prompt})
    
    # Format as chat template
    prompt = model.apply_chat_template(messages, tokenize=False)
    
    try:
        output = model(
            prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["User:", "Human:"]
        )
        content = output['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        # Fallback for simulation
        content = f"This is a simulated response for turn {current_turn}. I am experiencing the moment now."
    
    return {"role": "assistant", "content": content}

def run_turing_simulation(config: Dict[str, Any], 
                          num_turns: int = 20,
                          num_simulations: int = 5) -> Dict[str, Any]:
    """
    Run the full Turing simulation pipeline.
    
    Args:
        config: Configuration dictionary
        num_turns: Number of dialogue turns per simulation
        num_simulations: Number of independent simulations to run
    
    Returns:
        Aggregated results with distinction metrics
    """
    logger.info(f"Starting Turing simulation with {num_simulations} runs, {num_turns} turns each")
    
    # Load model
    model, _ = load_model_and_tokenizer(config)
    
    # Persona prompt for first-person experience
    persona_prompt = (
        "You are a conscious entity experiencing the world in first-person. "
        "Maintain a consistent persona throughout the conversation. "
        "Use sensory, temporal, and intentional language to describe your experiences. "
        "Do not break character or refer to yourself in the third person. "
        "Be specific about your internal state."
    )
    
    results = []
    detector = ContradictionDetector(config)
    
    for sim_idx in range(num_simulations):
        logger.info(f"Running simulation {sim_idx + 1}/{num_simulations}")
        
        dialogue = []
        for turn in range(num_turns):
            # Alternate between user and assistant
            if turn % 2 == 0:
                # User turn (simulated)
                user_prompts = [
                    "What do you notice?",
                    "How does that feel?",
                    "Tell me more.",
                    "What's happening now?",
                    "Describe your state.",
                ]
                user_text = random.choice(user_prompts)
                dialogue.append({"role": "user", "content": user_text})
            else:
                # Model turn
                turn_response = generate_dialogue_turn(
                    model, dialogue, num_turns, turn, persona_prompt
                )
                dialogue.append(turn_response)
            
            # Small delay to simulate real interaction
            time.sleep(0.1)
        
        # Analyze the dialogue
        analysis = detector.detect_contradictions(dialogue)
        analysis['simulation_id'] = sim_idx
        analysis['num_turns'] = num_turns
        results.append(analysis)
    
    # Aggregate results
    aggregated = {
        'num_simulations': num_simulations,
        'turns_per_simulation': num_turns,
        'individual_results': results,
        'summary': {}
    }
    
    # Compute aggregate metrics
    total_contradictions = sum(r['metrics']['total_contradictions'] for r in results)
    total_persona_breaks = sum(r['metrics']['total_persona_breaks'] for r in results)
    total_loops = sum(r['metrics']['total_repetition_loops'] for r in results)
    total_turns = sum(r['total_turns'] for r in results)
    
    avg_contradiction_rate = sum(r['metrics']['contradiction_rate'] for r in results) / len(results)
    avg_persona_break_rate = sum(r['metrics']['persona_break_rate'] for r in results) / len(results)
    avg_overall_score = sum(r['metrics']['overall_distinction_score'] for r in results) / len(results)
    
    aggregated['summary'] = {
        'average_contradiction_rate': avg_contradiction_rate,
        'average_persona_break_rate': avg_persona_break_rate,
        'average_overall_distinction_score': avg_overall_score,
        'total_contradictions_detected': total_contradictions,
        'total_persona_breaks_detected': total_persona_breaks,
        'total_repetition_loops_detected': total_loops,
        'total_turns_analyzed': total_turns,
        'interpretation': "Lower distinction scores indicate better sustained first-person coherence."
    }
    
    return aggregated

def main():
    """Main entry point for Turing simulation."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Load config
    config = get_config()
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run Turing Simulation for first-person dialogue consistency")
    parser.add_argument('--turns', type=int, default=20, help='Number of turns per simulation')
    parser.add_argument('--simulations', type=int, default=5, help='Number of simulations to run')
    parser.add_argument('--output', type=str, default='data/processed/turing_simulation_results.json',
                      help='Output file path')
    args = parser.parse_args()
    
    logger.info(f"Running Turing simulation: {args.simulations} runs, {args.turns} turns each")
    
    # Run simulation
    results = run_turing_simulation(
        config, 
        num_turns=args.turns, 
        num_simulations=args.simulations
    )
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    safe_write_json(results, output_path)
    logger.info(f"Results saved to {output_path}")
    
    # Print summary
    summary = results['summary']
    logger.info("=" * 60)
    logger.info("TURING SIMULATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Simulations: {summary['total_turns_analyzed']}")
    logger.info(f"Avg Contradiction Rate: {summary['average_contradiction_rate']:.4f}")
    logger.info(f"Avg Persona Break Rate: {summary['average_persona_break_rate']:.4f}")
    logger.info(f"Avg Overall Distinction Score: {summary['average_overall_distinction_score']:.4f}")
    logger.info(f"Total Contradictions: {summary['total_contradictions_detected']}")
    logger.info(f"Total Persona Breaks: {summary['total_persona_breaks_detected']}")
    logger.info("=" * 60)
    
    return results

if __name__ == '__main__':
    main()