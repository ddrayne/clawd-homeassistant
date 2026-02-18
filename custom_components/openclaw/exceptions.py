"""Exceptions for the OpenClaw integration."""


class OpenClawError(Exception):
    """Base exception for OpenClaw integration."""


class GatewayConnectionError(OpenClawError):
    """Cannot connect to Gateway."""


class GatewayAuthenticationError(OpenClawError):
    """Authentication failed - invalid token."""


class DevicePairingRequiredError(GatewayAuthenticationError):
    """Device is registered but not yet approved in OpenClaw."""


class GatewayTimeoutError(OpenClawError):
    """Request timeout - Gateway or agent took too long."""


class AgentExecutionError(OpenClawError):
    """Agent execution failed."""


class ProtocolError(OpenClawError):
    """Protocol version mismatch or invalid message."""
