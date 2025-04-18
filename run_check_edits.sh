#!/bin/bash

cd /path/to/daily-lotus  # set this to your project root

# Activate your virtual environment (if using one)
source .venv/bin/activate  # or use `eval "$(uv venv activate)"` if using uv venv

# Run the check with logging
uv run daily_lotus/check_edits.py >> logs/check_edits.log 2>&1
