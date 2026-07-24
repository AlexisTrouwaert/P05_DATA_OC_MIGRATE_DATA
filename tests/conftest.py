import os
import sys

# Make sure `migrate.py`, at the project root, is importable regardless of
# how pytest is invoked (plain `pytest`, `python -m pytest`, from another cwd...).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
