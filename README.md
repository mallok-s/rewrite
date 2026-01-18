# Rewrite

A CLI tool that converts Python variables to functions.

## Why?

In large Python codebases, converting module-level variables to functions can improve testability, lazy evaluation, and allow for dynamic configuration. This tool automates the refactoring process.

## Features

- Converts `lowercase_snake_case` variables to functions
- Automatically updates all usage sites within the same module
- Handles both `from module import var` and `import module` styles
- Supports aliased imports
- Dry-run mode by default (safe!)
- Clear output showing exactly what will change

## Installation

```bash
uv venv
uv pip install -e .

# For development (includes ruff)
uv pip install -e ".[dev]"
```

## Usage

### First Run (prompts for glob pattern)

```bash
uv run rewrite path/to/my_fields.py
# Prompts: "Pattern: " → enter "*_fields.py"
```

### Subsequent Runs

```bash
# Dry-run (default)
uv run rewrite path/to/my_fields.py

# Apply changes
uv run rewrite path/to/my_fields.py --apply

# Override saved pattern
uv run rewrite path/to/other_file.py --pattern "*.py" --apply
```

## Example

**Before:**
```python
# config.py
database_url = "postgresql://localhost/db"
max_retries = 3

# app.py
from config import database_url, max_retries

def connect():
    for i in range(max_retries):
        connect_to(database_url)
```

**After running `uv run rewrite config.py --pattern "*.py" --apply`:**
```python
# config.py
def database_url():
    return "postgresql://localhost/db"

def max_retries():
    return 3

# app.py
from config import database_url, max_retries

def connect():
    for i in range(max_retries()):
        connect_to(database_url())
```

## Safety Features

- **Dry-run by default**: See changes before applying
- **Pattern validation**: Only processes files matching glob pattern
- **Module-scoped**: Only modifies files in the same Python module
- **Clear warnings**: Alerts about skipped patterns (multiple assignments, star imports)

## What Gets Converted?

- Module-level variables following `lowercase_snake_case`
- Simple assignments: `var_name = value`

## What Gets Skipped?

- Multiple assignments: `a = b = value` (warns)
- Tuple unpacking: `a, b = 1, 2` (warns)
- Star imports: `from module import *` (warns)
- Variables starting with `_` (private)
- Variables not following `lowercase_snake_case`

## Configuration

The glob pattern is saved in `~/.config/rewrite/config.json` after first use and can be overridden with `--pattern`.

## Development

### Code Quality

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check code quality
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```
