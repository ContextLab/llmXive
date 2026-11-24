# This wrapper script simply invokes the download pipeline.
# It exists so that the quickstart can call a single entry point.
from code.data.download import main

if __name__ == "__main__":
    main()