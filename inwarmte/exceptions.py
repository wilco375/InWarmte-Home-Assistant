"""Exceptions for InWarmte"""


class InWarmteException(Exception):
    """Base exception of the InWarmte client"""
    pass


class InWarmteUnauthenticatedException(InWarmteException):
    """An attempt is made to perform a request which requires authentication while the client is not authenticated."""
    pass


class InWarmteConnectionException(InWarmteException):
    """An error occured in the connection with the API."""
    pass
