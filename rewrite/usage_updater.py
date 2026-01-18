"""Update usage sites of converted variables."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportInfo:
    """Information about an imported variable."""

    original_name: str  # Name in the source module
    alias: str  # Name used in this file (same as original_name if no alias)
    import_type: str  # 'from' or 'direct'
    module_name: str  # The module it's imported from


@dataclass
class UsageUpdate:
    """Represents a usage that needs to be updated."""

    lineno: int
    col_offset: int
    original: str
    updated: str
    import_info: ImportInfo


@dataclass
class StarImportWarning:
    """Warning about a star import that can't be automatically updated."""

    lineno: int
    module_name: str


def get_module_name_from_file(target_file, current_file, module_root):
    """
    Get the module import name for target_file from current_file's perspective.

    Args:
        target_file: Path to the file being converted
        current_file: Path to the file that imports from target_file
        module_root: Path to the module root

    Returns:
        str: The module name (e.g., 'config' or 'submodule.config')
    """
    target_path = Path(target_file).resolve()
    module_root_path = Path(module_root).resolve()

    # Get relative path from module root
    try:
        rel_path = target_path.relative_to(module_root_path)
    except ValueError:
        # Not in the same module root
        return None

    # Convert path to module name
    parts = list(rel_path.parts[:-1]) + [rel_path.stem]
    module_name = ".".join(parts)

    return module_name


def analyze_imports(file_path, target_module, converted_vars):
    """
    Analyze imports in a file to find which converted variables are imported.

    Args:
        file_path: Path to the file to analyze
        target_module: Module name of the target file (e.g., 'config')
        converted_vars: Set of variable names that were converted

    Returns:
        tuple: (dict of {alias: ImportInfo}, list of StarImportWarning)
    """
    with open(file_path) as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}, []

    imports = {}
    star_warnings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Handle: from module import name [as alias]
            if node.module == target_module or (
                node.module and target_module.endswith(node.module)
            ):
                for alias in node.names:
                    if alias.name == "*":
                        # Star import - can't reliably handle
                        star_warnings.append(
                            StarImportWarning(lineno=node.lineno, module_name=node.module)
                        )
                    elif alias.name in converted_vars:
                        # This is one of our converted variables
                        imported_as = alias.asname if alias.asname else alias.name
                        imports[imported_as] = ImportInfo(
                            original_name=alias.name,
                            alias=imported_as,
                            import_type="from",
                            module_name=node.module,
                        )

        elif isinstance(node, ast.Import):
            # Handle: import module [as alias]
            for alias in node.names:
                if alias.name == target_module or target_module.startswith(alias.name + "."):
                    # Store the module import
                    imported_as = alias.asname if alias.asname else alias.name
                    imports[f"__module__{imported_as}"] = ImportInfo(
                        original_name=alias.name,
                        alias=imported_as,
                        import_type="direct",
                        module_name=alias.name,
                    )

    return imports, star_warnings


class UsageTransformer(ast.NodeTransformer):
    """Transform variable usages to function calls."""

    def __init__(self, imports, converted_vars, target_module, source):
        """
        Initialize the transformer.

        Args:
            imports: Dict of {alias: ImportInfo}
            converted_vars: Set of converted variable names
            target_module: The target module name
            source: Original source code (for extracting source segments)
        """
        self.imports = imports
        self.converted_vars = converted_vars
        self.target_module = target_module
        self.source = source
        self.updates = []

    def visit_Name(self, node):
        """Visit Name nodes (simple variable references)."""
        # Check if this name is an imported converted variable
        if node.id in self.imports:
            import_info = self.imports[node.id]
            if import_info.import_type == "from":
                # This is a direct usage of a converted variable
                # Convert: var → var()
                original = node.id
                updated = f"{node.id}()"

                self.updates.append(
                    UsageUpdate(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        original=original,
                        updated=updated,
                        import_info=import_info,
                    )
                )

                # Return a Call node
                return ast.Call(
                    func=node, args=[], keywords=[], lineno=node.lineno, col_offset=node.col_offset
                )

        return self.generic_visit(node)

    def visit_Attribute(self, node):
        """Visit Attribute nodes (module.var references)."""
        # Check if this is a module.variable access
        if isinstance(node.value, ast.Name):
            module_key = f"__module__{node.value.id}"
            if module_key in self.imports and node.attr in self.converted_vars:
                # This is module.var where var was converted
                # Convert: module.var → module.var()
                original = f"{node.value.id}.{node.attr}"
                updated = f"{node.value.id}.{node.attr}()"

                import_info = self.imports[module_key]

                self.updates.append(
                    UsageUpdate(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        original=original,
                        updated=updated,
                        import_info=import_info,
                    )
                )

                # Return a Call node
                return ast.Call(
                    func=node, args=[], keywords=[], lineno=node.lineno, col_offset=node.col_offset
                )

        return self.generic_visit(node)


def update_usage_file(file_path, target_file, module_root, converted_vars):
    """
    Update a file to convert variable usages to function calls.

    Args:
        file_path: Path to the file to update
        target_file: Path to the target file (being converted)
        module_root: Path to the module root
        converted_vars: Set of variable names that were converted

    Returns:
        tuple: (updated source code, list of UsageUpdate, list of StarImportWarning)
    """
    # Get the module name for the target file
    target_module = get_module_name_from_file(target_file, file_path, module_root)

    if not target_module:
        # Not in the same module
        return None, [], []

    with open(file_path) as f:
        source = f.read()

    # Analyze imports
    imports, star_warnings = analyze_imports(file_path, target_module, converted_vars)

    # If no relevant imports, nothing to update
    if not imports and not star_warnings:
        return None, [], []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, [], star_warnings

    # Transform usages
    transformer = UsageTransformer(imports, converted_vars, target_module, source)
    new_tree = transformer.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source code
    if transformer.updates:
        new_source = ast.unparse(new_tree)
        return new_source, transformer.updates, star_warnings
    else:
        return None, [], star_warnings
