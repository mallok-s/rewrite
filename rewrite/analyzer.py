"""AST analyzer to identify variables to convert."""

import ast
import re
from dataclasses import dataclass


@dataclass
class Variable:
    """Represents a variable to be converted."""

    name: str
    lineno: int
    value_node: ast.expr
    value_source: str


@dataclass
class SkippedPattern:
    """Represents a pattern that was skipped."""

    lineno: int
    reason: str
    source: str


def is_lowercase_snake_case(name):
    """Check if a name follows lowercase_snake_case convention."""
    pattern = r"^[a-z][a-z0-9_]*$"
    return re.match(pattern, name) is not None


def analyze_file(file_path):
    """
    Analyze a Python file to find variables to convert.

    Args:
        file_path: Path to the Python file

    Returns:
        tuple: (list of Variable objects, list of SkippedPattern objects)
    """
    with open(file_path) as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {file_path}: {e}") from e

    variables = []
    skipped = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # Only process module-level assignments
            if node.col_offset != 0:
                continue

            # Check for multiple assignments (a = b = value)
            if len(node.targets) > 1:
                source_line = ast.get_source_segment(source, node)
                skipped.append(
                    SkippedPattern(
                        lineno=node.lineno,
                        reason="multiple assignment",
                        source=source_line or "<unknown>",
                    )
                )
                continue

            target = node.targets[0]

            # Check for tuple unpacking (a, b = 1, 2)
            if isinstance(target, ast.Tuple):
                source_line = ast.get_source_segment(source, node)
                skipped.append(
                    SkippedPattern(
                        lineno=node.lineno,
                        reason="tuple unpacking",
                        source=source_line or "<unknown>",
                    )
                )
                continue

            # Only process simple Name assignments
            if not isinstance(target, ast.Name):
                continue

            var_name = target.id

            # Skip if it doesn't match lowercase_snake_case
            if not is_lowercase_snake_case(var_name):
                continue

            # Skip private variables (starting with _)
            if var_name.startswith("_"):
                continue

            # Get the source code for the value
            value_source = ast.get_source_segment(source, node.value)

            variables.append(
                Variable(
                    name=var_name,
                    lineno=node.lineno,
                    value_node=node.value,
                    value_source=value_source or "<unknown>",
                )
            )

    return variables, skipped
