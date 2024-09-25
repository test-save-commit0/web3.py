class FallbackFn:
    """
    Represents a fallback function in Solidity contracts.
    """
    def __init__(self):
        self.selector = b''
        self.abi = {
            'type': 'fallback',
            'stateMutability': 'payable'
        }

    def __str__(self):
        return '<fallback>'

    def __repr__(self):
        return f'FallbackFn()'


class ReceiveFn:
    """
    Represents a receive function in Solidity contracts.
    """
    def __init__(self):
        self.selector = b''
        self.abi = {
            'type': 'receive',
            'stateMutability': 'payable'
        }

    def __str__(self):
        return '<receive>'

    def __repr__(self):
        return f'ReceiveFn()'
