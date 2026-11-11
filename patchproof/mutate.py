"""Single-point AST mutations: the bug injector, and the search repairer's patch space."""
import ast

_SWAPS = {
    ast.Lt: (ast.LtE, ast.Gt), ast.LtE: (ast.Lt,), ast.Gt: (ast.GtE, ast.Lt), ast.GtE: (ast.Gt,),
    ast.Eq: (ast.NotEq,), ast.NotEq: (ast.Eq,),
    ast.Add: (ast.Sub,), ast.Sub: (ast.Add,), ast.Mult: (ast.Add,), ast.FloorDiv: (ast.Mult,),
    ast.Mod: (ast.FloorDiv,), ast.And: (ast.Or,), ast.Or: (ast.And,),
}


def mutants(source):
    """Every program one mutation away from `source`, deduplicated, in source order."""
    tree = ast.parse(source)
    out = []

    def emit():
        out.append(ast.unparse(tree))

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                for alt in _SWAPS.get(type(op), ()):
                    node.ops[i] = alt()
                    emit()
                node.ops[i] = op
        elif isinstance(node, (ast.BinOp, ast.BoolOp, ast.AugAssign)):
            op = node.op
            for alt in _SWAPS.get(type(op), ()):
                node.op = alt()
                emit()
            node.op = op
        elif isinstance(node, ast.Constant) and type(node.value) is int:
            value = node.value
            for alt in (value + 1, value - 1):
                node.value = alt
                emit()
            node.value = value
    original = ast.unparse(tree)
    return [m for m in dict.fromkeys(out) if m != original]
