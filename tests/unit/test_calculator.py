"""Tests Calculator — couverture élevée via pytest.mark.parametrize."""

import math

import pytest

from app.calculator import Calculator, CalculatorError


# ──────────────────────────────────────────────────────────────────────────
#  Opérations unitaires
# ──────────────────────────────────────────────────────────────────────────
class TestAdd:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (2, 3, 5),
            (-1, 1, 0),
            (0, 0, 0),
            (1.5, 2.25, 3.75),
            (-2.5, -2.5, -5.0),
            (1e10, 1, 1e10 + 1),
        ],
    )
    def test_add(self, a, b, expected):
        assert Calculator.add(a, b) == expected


class TestSubtract:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (5, 2, 3),
            (0, 5, -5),
            (-5, -3, -2),
            (10.5, 0.5, 10.0),
        ],
    )
    def test_subtract(self, a, b, expected):
        assert Calculator.subtract(a, b) == expected


class TestMultiply:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (4, 3, 12),
            (-2, 5, -10),
            (-3, -3, 9),
            (0, 100, 0),
            (1.5, 2, 3.0),
        ],
    )
    def test_multiply(self, a, b, expected):
        assert Calculator.multiply(a, b) == expected


class TestDivide:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (10, 4, 2.5),
            (9, 3, 3),
            (-10, 2, -5),
            (1, 4, 0.25),
        ],
    )
    def test_divide(self, a, b, expected):
        assert Calculator.divide(a, b) == expected

    @pytest.mark.parametrize("a", [1, -1, 0, 3.14])
    def test_divide_by_zero(self, a):
        with pytest.raises(CalculatorError, match="Division par z"):
            Calculator.divide(a, 0)


class TestPower:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (2, 10, 1024),
            (2, 0, 1),
            (5, 1, 5),
            (4, 0.5, 2.0),
            (2, -1, 0.5),
        ],
    )
    def test_power(self, a, b, expected):
        assert Calculator.power(a, b) == expected


class TestSqrt:
    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 0),
            (1, 1),
            (4, 2),
            (9, 3),
            (2, math.sqrt(2)),
            (0.25, 0.5),
        ],
    )
    def test_sqrt(self, a, expected):
        assert math.isclose(Calculator.sqrt(a), expected)

    @pytest.mark.parametrize("a", [-1, -0.0001, -100])
    def test_sqrt_negative(self, a):
        with pytest.raises(CalculatorError, match="n.gatif"):
            Calculator.sqrt(a)


class TestModulo:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (10, 3, 1),
            (9, 3, 0),
            (7, 5, 2),
            (5.5, 2, 1.5),
        ],
    )
    def test_modulo(self, a, b, expected):
        assert Calculator.modulo(a, b) == expected

    @pytest.mark.parametrize("a", [1, 0, 5, -3])
    def test_modulo_zero(self, a):
        with pytest.raises(CalculatorError, match="Modulo par z"):
            Calculator.modulo(a, 0)


# ──────────────────────────────────────────────────────────────────────────
#  calculate(expression) — cas valides
# ──────────────────────────────────────────────────────────────────────────
class TestCalculateValid:
    @pytest.mark.parametrize(
        "expr,expected",
        [
            ("1 + 1", 2),
            ("2 - 5", -3),
            ("3 * 4", 12),
            ("8 / 2", 4),
            ("1 + 2 * 3", 7),                  # priorité
            ("(1 + 2) * 3", 9),                # parenthèses
            ("((1 + 2) * (3 + 4))", 21),       # imbriquées
            ("1.5 + 2.25", 3.75),              # décimaux
            ("  10   /   4  ", 2.5),           # espaces
            ("-3 + 5", 2),                     # unaire -
            ("+3 + 5", 8),                     # unaire +
            ("-(2 + 3)", -5),
            ("10 / 4 * 2", 5.0),               # associativité gauche
            ("1 - 2 - 3", -4),
        ],
    )
    def test_calculate(self, expr, expected):
        assert math.isclose(
            Calculator.calculate(expr), expected, rel_tol=1e-9, abs_tol=1e-9
        )


# ──────────────────────────────────────────────────────────────────────────
#  calculate(expression) — cas invalides
# ──────────────────────────────────────────────────────────────────────────
class TestCalculateInvalid:
    @pytest.mark.parametrize(
        "expr,pattern",
        [
            ("1 / 0", "Division par z"),
            ("5 / (2 - 2)", "Division par z"),
            ("__import__('os')", "Caract"),
            ("a + b", "Caract"),
            ("1 + 2;", "Caract"),
            ("2 ** 3", "Op.rateur binaire"),
            ("", "vide"),
            ("   ", "vide"),
        ],
    )
    def test_invalid_message(self, expr, pattern):
        with pytest.raises(CalculatorError, match=pattern):
            Calculator.calculate(expr)

    @pytest.mark.parametrize(
        "expr",
        [
            "1 +",
            "* 2",
            "(1 + 2",
            "1 + 2)",
            "..",
            "1..2 + 3",
        ],
    )
    def test_invalid_syntax(self, expr):
        with pytest.raises(CalculatorError):
            Calculator.calculate(expr)

    @pytest.mark.parametrize("value", [None, 123, 1.5, [], {}, ("1+1",)])
    def test_non_string(self, value):
        with pytest.raises(CalculatorError, match="cha"):
            Calculator.calculate(value)


# ──────────────────────────────────────────────────────────────────────────
#  Sécurité — l'AST refuse tout sauf nombres et + - * /
# ──────────────────────────────────────────────────────────────────────────
class TestSecurity:
    @pytest.mark.parametrize(
        "expr",
        [
            "open('f')",
            "x",
            "[1, 2]",
            "1 if 1 else 0",
            "lambda x: x",
        ],
    )
    def test_dangerous_constructs_blocked(self, expr):
        with pytest.raises(CalculatorError):
            Calculator.calculate(expr)
