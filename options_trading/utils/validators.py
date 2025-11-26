"""
Validation utility functions.

This module provides input validation helpers for the options trading system.
"""

from typing import Any, Union


def validate_positive(value: Union[int, float], name: str = "Value") -> None:
    """
    Validate that a value is positive.
    
    Args:
        value: Value to validate
        name: Name to use in error message
        
    Raises:
        ValueError: If value is not positive
        TypeError: If value is not numeric
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_non_negative(value: Union[int, float], name: str = "Value") -> None:
    """
    Validate that a value is non-negative.
    
    Args:
        value: Value to validate
        name: Name to use in error message
        
    Raises:
        ValueError: If value is negative
        TypeError: If value is not numeric
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def validate_probability(value: Union[int, float], name: str = "Probability") -> None:
    """
    Validate that a value is a valid probability (between 0 and 1).
    
    Args:
        value: Value to validate
        name: Name to use in error message
        
    Raises:
        ValueError: If value is not between 0 and 1
        TypeError: If value is not numeric
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value).__name__}")
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def validate_in_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    name: str = "Value"
) -> None:
    """
    Validate that a value is within a specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        name: Name to use in error message
        
    Raises:
        ValueError: If value is outside the range
        TypeError: If value is not numeric
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value).__name__}")
    if value < min_val or value > max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
