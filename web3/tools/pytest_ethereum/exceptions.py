class PytestEthereumError(Exception):
    """
    Base class for all Pytest-Ethereum errors.
    """
    def __init__(self, message="An error occurred in Pytest-Ethereum"):
        self.message = message
        super().__init__(self.message)


class DeployerError(PytestEthereumError):
    """
    Raised when the Deployer is unable to deploy a contract type.
    """
    def __init__(self, message="Unable to deploy contract"):
        super().__init__(message)


class LinkerError(PytestEthereumError):
    """
    Raised when the Linker is unable to link two contract types.
    """
    def __init__(self, message="Unable to link contract types"):
        super().__init__(message)
