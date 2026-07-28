import pytest
from utils import normalize_text, jaccard_similarity, tokenize_simple

def test_nfk_normalization_handles_emoji():
    """
    Test that NFKC normalization correctly handles emoji characters.
    
    DailyDialog dataset may contain emoji characters in dialogue turns.
    NFKC normalization should preserve emoji while normalizing other characters.
    """
    # Test case 1: Emoji should be preserved
    text_with_emoji = "Hello 👋 World 🌍"
    normalized = normalize_text(text_with_emoji)
    assert "👋" in normalized, "Emoji 👋 should be preserved after NFKC normalization"
    assert "🌍" in normalized, "Emoji 🌍 should be preserved after NFKC normalization"
    assert "Hello" in normalized, "Text 'Hello' should be preserved"
    assert "World" in normalized, "Text 'World' should be preserved"
    
    # Test case 2: Fullwidth characters should be normalized to ASCII
    # Fullwidth 'H' (U+FF21) should become 'H' (U+0048)
    fullwidth_text = "Hello"  # Fullwidth characters
    normalized_fullwidth = normalize_text(fullwidth_text)
    assert normalized_fullwidth == "Hello", f"Fullwidth characters should be normalized to ASCII, got: {normalized_fullwidth}"
    
    # Test case 3: Emoji composed with skin tone modifiers
    # 👍🏻 (thumbs up with light skin tone) should be preserved
    skin_tone_emoji = "👍🏻"
    normalized_skin = normalize_text(skin_tone_emoji)
    assert "👍" in normalized_skin or skin_tone_emoji in normalized_skin, \
        "Emoji with skin tone modifiers should be preserved"
    
    # Test case 4: Mixed content - text, emoji, and special characters
    mixed_text = "Great job! 👏🎉 Thanks 100%"
    normalized_mixed = normalize_text(mixed_text)
    assert "👏" in normalized_mixed and "🎉" in normalized_mixed, \
        "Multiple emojis should be preserved in mixed content"
    assert "Great job!" in normalized_mixed and "100%" in normalized_mixed, \
        "Text and numbers should be preserved in mixed content"

def test_jaccard_similarity_identical_sets():
    """
    Test that Jaccard similarity returns 1.0 for identical sets.
    """
    set1 = {"hello", "world", "test"}
    set2 = {"hello", "world", "test"}
    
    result = jaccard_similarity(set1, set2)
    assert result == 1.0, f"Identical sets should have Jaccard similarity of 1.0, got {result}"

def test_jaccard_similarity_disjoint_sets():
    """
    Test that Jaccard similarity returns 0.0 for disjoint sets.
    """
    set1 = {"hello", "world"}
    set2 = {"foo", "bar"}
    
    result = jaccard_similarity(set1, set2)
    assert result == 0.0, f"Disjoint sets should have Jaccard similarity of 0.0, got {result}"

def test_jaccard_similarity_partial_overlap():
    """
    Test Jaccard similarity with partial overlap.
    Jaccard = |A ∩ B| / |A ∪ B|
    A = {1, 2, 3}, B = {2, 3, 4}
    Intersection = {2, 3} (size 2)
    Union = {1, 2, 3, 4} (size 4)
    Result = 2/4 = 0.5
    """
    set1 = {1, 2, 3}
    set2 = {2, 3, 4}
    
    result = jaccard_similarity(set1, set2)
    assert result == 0.5, f"Partial overlap should yield 0.5, got {result}"

def test_jaccard_similarity_empty_sets():
    """
    Test that Jaccard similarity returns 0.0 when both sets are empty.
    """
    set1 = set()
    set2 = set()
    
    result = jaccard_similarity(set1, set2)
    # By convention, Jaccard of two empty sets is 0.0 (or undefined, but 0.0 is safe)
    assert result == 0.0, f"Empty sets should have Jaccard similarity of 0.0, got {result}"

def test_jaccard_similarity_one_empty_set():
    """
    Test that Jaccard similarity returns 0.0 when one set is empty.
    """
    set1 = {"hello", "world"}
    set2 = set()
    
    result = jaccard_similarity(set1, set2)
    assert result == 0.0, f"Empty and non-empty sets should have Jaccard similarity of 0.0, got {result}"

def test_jaccard_similarity_case_sensitivity():
    """
    Test that Jaccard similarity is case-sensitive by default.
    """
    set1 = {"Hello", "World"}
    set2 = {"hello", "world"}
    
    result = jaccard_similarity(set1, set2)
    assert result == 0.0, f"Case-sensitive comparison should yield 0.0, got {result}"

def test_jaccard_similarity_single_element():
    """
    Test Jaccard similarity with single element sets.
    """
    set1 = {"a"}
    set2 = {"a"}
    
    result = jaccard_similarity(set1, set2)
    assert result == 1.0, f"Single identical elements should yield 1.0, got {result}"
    
    set3 = {"a"}
    set4 = {"b"}
    
    result2 = jaccard_similarity(set3, set4)
    assert result2 == 0.0, f"Single different elements should yield 0.0, got {result2}"

def test_jaccard_similarity_with_tokenized_text():
    """
    Test Jaccard similarity using tokenized text from the utility functions.
    """
    text1 = "hello world"
    text2 = "hello there"
    
    tokens1 = set(tokenize_simple(text1))
    tokens2 = set(tokenize_simple(text2))
    
    result = jaccard_similarity(tokens1, tokens2)
    # tokens1 = {"hello", "world"}, tokens2 = {"hello", "there"}
    # Intersection = {"hello"} (size 1)
    # Union = {"hello", "world", "there"} (size 3)
    # Result = 1/3 ≈ 0.333
    assert abs(result - 1/3) < 0.0001, f"Expected ~0.333, got {result}"

def test_jaccard_similarity_with_pos_tags():
    """
    Test Jaccard similarity using POS tags (simulated).
    """
    # Simulated POS tag sets for two utterances
    pos_tags_1 = {"NN", "VB", "DT"}  # Noun, Verb, Determiner
    pos_tags_2 = {"NN", "VB", "JJ"}  # Noun, Verb, Adjective
    
    result = jaccard_similarity(pos_tags_1, pos_tags_2)
    # Intersection = {"NN", "VB"} (size 2)
    # Union = {"NN", "VB", "DT", "JJ"} (size 4)
    # Result = 2/4 = 0.5
    assert result == 0.5, f"Expected 0.5 for POS tag overlap, got {result}"