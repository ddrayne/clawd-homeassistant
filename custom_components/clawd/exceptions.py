"""Exceptions for the Clawd integration."""


class ClawdError(Exception):
    """Base exception for Clawd integration."""


class GatewayConnectionError(ClawdError):
    """Cannot connect to Gateway."""


class GatewayAuthenticationError(ClawdError):
    """Authentication failed - invalid token."""


class GatewayTimeoutError(ClawdError):
    """Request timeout - Gateway or agent took too long."""


class AgentExecutionError(ClawdError):
    """Agent execution failed."""


class ProtocolError(ClawdError):
    """Protocol version mismatch or invalid message."""
