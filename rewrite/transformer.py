"""AST transformer to convert variables to functions."""

import ast


def create_function_node(variable):
    """
    Create a function definition AST node from a variable.

    Args:
        variable: Variable object to convert

    Returns:
        ast.FunctionDef: Function definition node
    """
    return ast.FunctionDef(
        name=variable.name,
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Return(value=variable.value_node)],
        decorator_list=[],
        lineno=variable.lineno,
        col_offset=0,
    )


class VariableToFunctionTransformer(ast.NodeTransformer):
    """Transforms variable assignments to function definitions."""

    def __init__(self, variables_to_convert):
        """
        Initialize the transformer.

        Args:
            variables_to_convert: Set of variable names to convert
        """
        self.variables_to_convert = variables_to_convert
        self.converted_count = 0

    def visit_Assign(self, node):
        """Visit assignment nodes and convert matching variables."""
        # Only process module-level assignments
        if node.col_offset != 0:
            return node

        # Only single target assignments
        if len(node.targets) != 1:
            return node

        target = node.targets[0]

        # Only simple name assignments
        if not isinstance(target, ast.Name):
            return node

        # Check if this variable should be converted
        if target.id in self.variables_to_convert:
            # Create a function from this variable
            func_node = ast.FunctionDef(
                name=target.id,
                args=ast.arguments(
                    posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
                ),
                body=[ast.Return(value=node.value)],
                decorator_list=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            self.converted_count += 1
            return func_node

        return node


def transform_file(file_path, variables):
    """
    Transform a file to convert variables to functions.

    Args:
        file_path: Path to the Python file
        variables: List of Variable objects to convert

    Returns:
        str: Transformed source code
    """
    with open(file_path) as f:
        source = f.read()

    tree = ast.parse(source)

    # Create a set of variable names to convert
    var_names = {var.name for var in variables}

    # Transform the AST
    transformer = VariableToFunctionTransformer(var_names)
    new_tree = transformer.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source code
    return ast.unparse(new_tree)
