"""Configuration management for the rewrite CLI tool."""

import json
from fnmatch import fnmatch
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "rewrite"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    """Load configuration from disk."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config):
    """Save configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_glob_pattern(pattern_override=None):
    """
    Get the glob pattern for filename validation.

    If pattern_override is provided, use it and save for future use.
    Otherwise, load from config or prompt user.

    Returns:
        str: The glob pattern to use
    """
    if pattern_override:
        config = load_config()
        config["glob_pattern"] = pattern_override
        save_config(config)
        return pattern_override

    config = load_config()
    if "glob_pattern" in config:
        return config["glob_pattern"]

    # First run - prompt user
    print("First-time setup: Please enter a glob pattern for target files.")
    print("Example: *_fields.py (matches files ending in '_fields.py')")
    pattern = input("Pattern: ").strip()

    if not pattern:
        pattern = "*.py"  # Default fallback

    config["glob_pattern"] = pattern
    save_config(config)
    print(f"Pattern '{pattern}' saved to {CONFIG_FILE}")

    return pattern


def validate_pattern(filename, pattern):
    """
    Validate that a filename matches the configured pattern.

    Args:
        filename: The filename to check
        pattern: The glob pattern to match against

    Returns:
        bool: True if filename matches pattern
    """
    return fnmatch(filename, pattern)
