# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CLI tool that converts Python variables to functions. The tool analyzes a target file, converts lowercase_snake_case variables to functions, and automatically updates all usage sites within the same Python module.

## Installation

```bash
# Create virtual environment
uv venv

# Install the package
uv pip install -e .

# Install with dev dependencies (includes ruff)
uv pip install -e ".[dev]"
```

## Running the Tool

```bash
# Dry-run (shows what will change)
uv run rewrite path/to/fields.py --pattern "*_fields.py"

# Apply changes
uv run rewrite path/to/fields.py --pattern "*_fields.py" --apply

# Pattern is saved after first run, so subsequent runs can omit it
uv run rewrite path/to/fields.py --apply
```

## Project Structure

```
rewrite/
├── rewrite/                # Main package
│   ├── cli.py             # CLI entry point
│   ├── config.py          # Config management (saves glob pattern)
│   ├── analyzer.py        # Variable identification (AST parsing)
│   ├── transformer.py     # AST transformation (var → function)
│   ├── scanner.py         # Module file discovery
│   ├── usage_updater.py   # Update usage sites with ()
│   └── output.py          # Output formatting
├── tests/                 # Test examples
└── pyproject.toml         # Package configuration
```

## How It Works

1. **Analyzes** target file to find lowercase_snake_case variables
2. **Converts** variables to functions: `var = value` → `def var(): return value`
3. **Scans** the Python module for files that import these variables
4. **Updates** all usage sites to add function calls: `var` → `var()`
5. Handles both import styles: `from module import var` and `import module`

## Edge Cases

- Skips multiple assignments (`a = b = value`) with warning
- Skips tuple unpacking with warning
- Skips star imports (`from module import *`) with warning
- Handles aliased imports correctly
- Only modifies files within the same Python module/package

## Code Quality

The project uses ruff for linting and formatting:

```bash
# Check code quality
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

Ruff is configured in `pyproject.toml` with rules for:
- pycodestyle (E, W)
- pyflakes (F)
- isort (I) - import sorting
- pep8-naming (N)
- pyupgrade (UP) - modern Python idioms
- flake8-bugbear (B)
- flake8-comprehensions (C4)
- flake8-simplify (SIM)
