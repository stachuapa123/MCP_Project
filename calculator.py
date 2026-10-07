"""The calculator itself: plain Python functions, no AI and no MCP.

Keeping the real logic here (separate from any LLM or MCP code) is a good habit.
Every later step only *wraps* these functions so a model can call them, and the
functions can be tested on their own (see tests/test_calculator.py).
"""

import math


def add(a: float, b: float) -> float:
    """Return a + b."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return a - b."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return a * b."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return a / b. Raises ValueError when b is 0."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


def power(base: float, exponent: float) -> float:
    """Return base raised to exponent."""
    return base**exponent


def sqrt(x: float) -> float:
    """Return the square root of x. Raises ValueError when x is negative."""
    if x < 0:
        raise ValueError("Cannot take the square root of a negative number.")
    return math.sqrt(x)

def factorial(x: float) -> float:
    if x < 0:
        raise ValueError("Cannot take factorial of a negative number")
    return math.factorial(x)
