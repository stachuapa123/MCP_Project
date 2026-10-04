import pytest

import calculator


def test_basic_operations():
    assert calculator.add(2, 3) == 5
    assert calculator.subtract(2, 3) == -1
    assert calculator.multiply(4, 2.5) == 10
    assert calculator.divide(9, 3) == 3
    assert calculator.power(2, 10) == 1024
    assert calculator.sqrt(144) == 12


def test_divide_by_zero():
    with pytest.raises(ValueError, match="divide by zero"):
        calculator.divide(1, 0)


def test_sqrt_of_negative():
    with pytest.raises(ValueError, match="negative"):
        calculator.sqrt(-1)
