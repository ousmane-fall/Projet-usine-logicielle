import math

import pytest

from app.calculator import Calculator, CalculatorError


class TestBasicOps:
    def test_add(self):
        assert Calculator.add(2, 3) == 5

    def test_subtract(self):
        assert Calculator.subtract(5, 2) == 3

    def test_multiply(self):
        assert Calculator.multiply(4, 3) == 12

    def test_divide(self):
        assert Calculator.divide(10, 4) == 2.5

    def test_divide_by_zero(self):
        with pytest.raises(CalculatorError, match="Division par z"):
            Calculator.divide(1, 0)

    def test_power(self):
        assert Calculator.power(2, 10) == 1024

    def test_sqrt(self):
        assert Calculator.sqrt(9) == 3
        assert math.isclose(Calculator.sqrt(2), math.sqrt(2))

    def test_sqrt_negative(self):
        with pytest.raises(CalculatorError, match="n.gatif"):
            Calculator.sqrt(-1)

    def test_modulo(self):
        assert Calculator.modulo(10, 3) == 1

    def test_modulo_zero(self):
        with pytest.raises(CalculatorError, match="Modulo par z"):
            Calculator.modulo(5, 0)


class TestExpression:
    def test_priority(self):
        assert Calculator.calculate("1 + 2 * 3") == 7

    def test_parentheses(self):
        assert Calculator.calculate("(1 + 2) * 3") == 9

    def test_decimals(self):
        assert math.isclose(Calculator.calculate("1.5 + 2.25"), 3.75)

    def test_unary_minus(self):
        assert Calculator.calculate("-3 + 5") == 2

    def test_spaces(self):
        assert Calculator.calculate("  10   /   4  ") == 2.5

    def test_division_by_zero(self):
        with pytest.raises(CalculatorError, match="Division par z"):
            Calculator.calculate("1 / 0")

    def test_forbidden_chars(self):
        with pytest.raises(CalculatorError, match="Caract"):
            Calculator.calculate("__import__('os')")

    def test_forbidden_power_operator(self):
        # ** n'est pas dans la whitelist de caractères
        with pytest.raises(CalculatorError):
            Calculator.calculate("2 ** 3")

    def test_empty(self):
        with pytest.raises(CalculatorError, match="vide"):
            Calculator.calculate("   ")

    def test_invalid_syntax(self):
        with pytest.raises(CalculatorError):
            Calculator.calculate("1 + ")
