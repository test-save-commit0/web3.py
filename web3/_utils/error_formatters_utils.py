import warnings
from eth_abi import abi
from eth_utils import to_bytes
from web3.exceptions import ContractCustomError, ContractLogicError, ContractPanicError, OffchainLookup, TransactionIndexingInProgress
from web3.types import RPCResponse
SOLIDITY_ERROR_FUNC_SELECTOR = '0x08c379a0'
OFFCHAIN_LOOKUP_FUNC_SELECTOR = '0x556f1830'
OFFCHAIN_LOOKUP_FIELDS = {'sender': 'address', 'urls': 'string[]',
    'callData': 'bytes', 'callbackFunction': 'bytes4', 'extraData': 'bytes'}
PANIC_ERROR_FUNC_SELECTOR = '0x4e487b71'
PANIC_ERROR_CODES = {'00':
    'Panic error 0x00: Generic compiler inserted panics.', '01':
    'Panic error 0x01: Assert evaluates to false.', '11':
    'Panic error 0x11: Arithmetic operation results in underflow or overflow.',
    '12': 'Panic error 0x12: Division by zero.', '21':
    'Panic error 0x21: Cannot convert value into an enum type.', '22':
    'Panic error 0x12: Storage byte array is incorrectly encoded.', '31':
    "Panic error 0x31: Call to 'pop()' on an empty array.", '32':
    'Panic error 0x32: Array index is out of bounds.', '41':
    'Panic error 0x41: Allocation of too much memory or array too large.',
    '51':
    'Panic error 0x51: Call to a zero-initialized variable of internal function type.'
    }
MISSING_DATA = 'no data'


def _parse_error_with_reverted_prefix(data: str) -> str:
    """
    Parse errors from the data string which begin with the "Reverted" prefix.
    "Reverted", function selector and offset are always the same for revert errors
    """
    if data.startswith('Reverted '):
        data = data[9:]  # Remove "Reverted " prefix
    if data.startswith('0x'):
        data = data[2:]  # Remove "0x" prefix if present
    if len(data) < 8 + 64 + 64:  # Minimum length for a valid revert error
        return MISSING_DATA
    # Skip function selector (4 bytes) and offset (32 bytes)
    error_data = data[8 + 64:]
    # Decode the error message
    try:
        error_message = abi.decode(['string'], to_bytes(hexstr=error_data))[0]
        return error_message
    except:
        return MISSING_DATA


def _raise_contract_error(response_error_data: str) -> None:
    """
    Decode response error from data string and raise appropriate exception.

        "Reverted " (prefix may be present in `data`)
        Function selector for Error(string): 08c379a (4 bytes)
        Data offset: 32 (32 bytes)
        String length (32 bytes)
        Reason string (padded, use string length from above to get meaningful part)
    """
    if response_error_data.startswith('Reverted '):
        response_error_data = response_error_data[9:]
    if response_error_data.startswith('0x'):
        response_error_data = response_error_data[2:]

    if response_error_data.startswith(SOLIDITY_ERROR_FUNC_SELECTOR[2:]):
        error_msg = _parse_error_with_reverted_prefix(response_error_data)
        raise ContractLogicError(error_msg)
    elif response_error_data.startswith(PANIC_ERROR_FUNC_SELECTOR[2:]):
        panic_code = response_error_data[8:10]
        panic_msg = PANIC_ERROR_CODES.get(panic_code, f"Unknown panic error code: {panic_code}")
        raise ContractPanicError(panic_msg)
    elif response_error_data.startswith(OFFCHAIN_LOOKUP_FUNC_SELECTOR[2:]):
        try:
            decoded = abi.decode(list(OFFCHAIN_LOOKUP_FIELDS.values()), to_bytes(hexstr=response_error_data[10:]))
            raise OffchainLookup(dict(zip(OFFCHAIN_LOOKUP_FIELDS.keys(), decoded)))
        except:
            raise ContractLogicError("Failed to decode OffchainLookup error")
    else:
        raise ContractCustomError(f"Unknown error: {response_error_data}")


def raise_contract_logic_error_on_revert(response: RPCResponse) -> RPCResponse:
    """
    Revert responses contain an error with the following optional attributes:
        `code` - in this context, used for an unknown edge case when code = '3'
        `message` - error message is passed to the raised exception
        `data` - response error details (str, dict, None)

    See also https://solidity.readthedocs.io/en/v0.6.3/control-structures.html#revert
    """
    if 'error' not in response:
        return response

    error = response['error']
    message = error.get('message', '')
    code = error.get('code')
    data = error.get('data')

    if code == 3:
        raise ContractLogicError(message)

    if isinstance(data, str):
        if data.startswith('Reverted ') or data.startswith('0x'):
            _raise_contract_error(data)
        else:
            raise ContractLogicError(data)
    elif isinstance(data, dict) and isinstance(data.get('message'), str):
        raise ContractLogicError(data['message'])
    elif message:
        raise ContractLogicError(message)
    else:
        raise ContractLogicError("Unspecified contract error")

    return response  # This line will never be reached, but it's kept for consistency


def raise_transaction_indexing_error_if_indexing(response: RPCResponse) -> RPCResponse:
    """
    Raise an error if ``eth_getTransactionReceipt`` returns an error indicating that
    transactions are still being indexed.
    """
    if 'error' in response:
        error = response['error']
        message = error.get('message', '')
        if 'still indexing' in message.lower():
            raise TransactionIndexingInProgress(message)
    return response
