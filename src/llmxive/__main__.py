"""Allow `python -m llmxive` to dispatch into cli.main()."""

from llmxive.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
