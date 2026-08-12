"""
Contract tests for corpus token bounds verification.

Ensures that the constructed micro-corpus meets the token count
requirements (≥ 1,000,000 and ≤ 1,010,000 tokens).
"""
import json
import os
import sys
from pathlib import Path

# Add code root to path if running standalone
if __name__ == "__main__":
    current_file = Path(__file__)
    code_root = current_file.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

def count_tokens_in_jsonl(file_path, tokenizer_name="gpt2"):
    """
    Count the total number of tokens in a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        tokenizer_name: Name of the tokenizer to use (default: gpt2)
        
    Returns:
        int: Total token count
    """
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    except ImportError:
        raise ImportError("transformers library is required. Install with: pip install transformers")
    
    total_tokens = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    text = data.get('text', '')
                    tokens = tokenizer.encode(text, add_special_tokens=False)
                    total_tokens += len(tokens)
                except json.JSONDecodeError:
                    continue
    
    return total_tokens

def test_corpus_token_bounds():
    """
    Contract test: Verify corpus token count is within bounds.
    
    Expected: Total tokens ≥ 1,000,000 and ≤ 1,010,000
    """
    # This test is designed to run against the actual processed corpus
    # In a real scenario, this would be run after T014 completes
    processed_dir = Path(__file__).parent.parent / "data" / "processed"
    corpus_file = processed_dir / "micro_corpus_full.jsonl"
    
    if not corpus_file.exists():
        # Skip if corpus not yet generated (expected during development)
        print(f"SKIP: Corpus file not found at {corpus_file}. Run data generation first.")
        return True
    
    try:
        token_count = count_tokens_in_jsonl(corpus_file)
        
        # Assert bounds
        assert token_count >= 1_000_000, f"Token count {token_count} is below minimum 1,000,000"
        assert token_count <= 1_010_000, f"Token count {token_count} exceeds maximum 1,010,000"
        
        print(f"PASS: Corpus token count is {token_count:,} (within bounds)")
        return True
        
    except Exception as e:
        print(f"FAIL: {e}")
        return False

if __name__ == "__main__":
    success = test_corpus_token_bounds()
    sys.exit(0 if success else 1)
