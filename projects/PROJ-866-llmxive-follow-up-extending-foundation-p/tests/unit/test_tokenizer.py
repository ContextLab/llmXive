"""
Unit test for the tokenizer wrapper defined in ``code/lib/utils.py``.
Verifies that the ``count_tokens`` function correctly counts tokens
using the ``cl100k_base`` model from the ``tiktoken`` library.
"""

from code.lib.utils import count_tokens


def test_hello_world_token_count():
    """
    The string ``"Hello world"`` should be tokenised into exactly two tokens
    with the ``cl100k_base`` encoding.
    """
    assert count_tokens("Hello world") == 2
