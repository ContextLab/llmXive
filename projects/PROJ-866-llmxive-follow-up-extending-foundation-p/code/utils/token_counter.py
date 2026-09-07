import tiktoken
from typing import Union


def count_tokens_cl100k_base(text: Union[str, bytes]) -> int:
    """Count tokens using the cl100k_base encoding.

    Args:
        text: Input text.

    Returns:
        Number of tokens.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    return len(encoding.encode(text))


def main() -> None:
    """Main entry point for token counter."""
    import argparse

    parser = argparse.ArgumentParser(description="Token Counter")
    parser.add_argument("--text", type=str, required=True, help="Text to count tokens for")

    args = parser.parse_args()

    count = count_tokens_cl100k_base(args.text)
    print(f"Token count: {count}")


if __name__ == "__main__":
    main()
