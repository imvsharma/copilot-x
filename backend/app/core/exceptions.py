"""Domain and HTTP-facing exceptions (maps to consistent API errors)."""


class CopilotXError(Exception):
    """Base error for business logic failures."""

    def __init__(self, message: str, code: str = "copilotx_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigurationError(CopilotXError):
    """Missing or invalid configuration (e.g. API key)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")


class ExternalServiceError(CopilotXError):
    """LLM, Redis, or MongoDB failures."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="external_service_error")
