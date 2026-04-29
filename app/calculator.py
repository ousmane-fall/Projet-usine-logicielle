"""Calculator: opérations arithmétiques et évaluation d'expressions.

Sécurité: l'évaluation d'expressions n'utilise PAS `eval`. Elle s'appuie sur
le module `ast` avec une whitelist stricte de noeuds (nombres et opérations
binaires +, -, *, /, plus l'unaire -). Toute autre construction (appel de
fonction, nom, attribut, etc.) est rejetée.
"""

import ast
import math
import operator
import re

Number = int | float

_ALLOWED_CHARS = re.compile(r"^[0-9\.\+\-\*\/\(\)\s]+$")

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorError(ValueError):
    """Erreur métier remontée par Calculator."""


class Calculator:
    """Opérations arithmétiques de base + évaluateur d'expression sûr."""

    @staticmethod
    def add(a: Number, b: Number) -> Number:
        return a + b

    @staticmethod
    def subtract(a: Number, b: Number) -> Number:
        return a - b

    @staticmethod
    def multiply(a: Number, b: Number) -> Number:
        return a * b

    @staticmethod
    def divide(a: Number, b: Number) -> float:
        if b == 0:
            raise CalculatorError("Division par zéro")
        return a / b

    @staticmethod
    def power(a: Number, b: Number) -> Number:
        return a ** b

    @staticmethod
    def sqrt(a: Number) -> float:
        if a < 0:
            raise CalculatorError("Racine carrée d'un nombre négatif")
        return math.sqrt(a)

    @staticmethod
    def modulo(a: Number, b: Number) -> Number:
        if b == 0:
            raise CalculatorError("Modulo par zéro")
        return a % b

    @classmethod
    def calculate(cls, expression: str) -> Number:
        """Évalue une expression arithmétique (+ - * /) avec priorité.

        - Supporte les décimaux, espaces et parenthèses.
        - Rejette tout caractère hors de [0-9 . + - * / ( ) espace].
        - N'utilise pas `eval`.
        """
        if not isinstance(expression, str):
            raise CalculatorError("L'expression doit être une chaîne de caractères")

        expr = expression.strip()
        if not expr:
            raise CalculatorError("Expression vide")

        if not _ALLOWED_CHARS.match(expr):
            raise CalculatorError("Caractères interdits dans l'expression")

        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise CalculatorError("Expression invalide") from exc

        return cls._eval_node(tree.body)

    @classmethod
    def _eval_node(cls, node: ast.AST) -> Number:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise CalculatorError("Constante non numérique interdite")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _BIN_OPS:
                raise CalculatorError("Opérateur binaire interdit")
            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)
            if op_type is ast.Div and right == 0:
                raise CalculatorError("Division par zéro")
            return _BIN_OPS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _UNARY_OPS:
                raise CalculatorError("Opérateur unaire interdit")
            return _UNARY_OPS[op_type](cls._eval_node(node.operand))

        raise CalculatorError("Construction non autorisée dans l'expression")
