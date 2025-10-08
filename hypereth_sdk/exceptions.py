"""
Custom exceptions for HyperETH SDK
"""


class HyperETHError(Exception):
    """Base exception for all HyperETH SDK errors"""
    pass


class AuthenticationError(HyperETHError):
    """Raised when authentication fails"""
    pass


class APIError(HyperETHError):
    """Raised when API request fails"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ValidationError(HyperETHError):
    """Raised when input validation fails"""
    pass


class SigningError(HyperETHError):
    """Raised when message signing fails"""
    pass