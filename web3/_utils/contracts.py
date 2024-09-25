import functools
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Sequence, Tuple, Type, Union, cast
from eth_abi.codec import ABICodec
from eth_abi.registry import registry as default_registry
from eth_typing import ChecksumAddress, HexStr, TypeStr
from eth_utils import add_0x_prefix, encode_hex, function_abi_to_4byte_selector, is_binary_address, is_checksum_address, is_list_like, is_text
from eth_utils.toolz import pipe
from hexbytes import HexBytes
from web3._utils.abi import abi_to_signature, check_if_arguments_can_be_encoded, filter_by_argument_count, filter_by_argument_name, filter_by_encodability, filter_by_name, filter_by_type, get_abi_input_types, get_aligned_abi_inputs, get_fallback_func_abi, get_receive_func_abi, map_abi_data, merge_args_and_kwargs, named_tree
from web3._utils.blocks import is_hex_encoded_block_hash
from web3._utils.encoding import to_hex
from web3._utils.function_identifiers import FallbackFn, ReceiveFn
from web3._utils.method_formatters import to_integer_if_hex
from web3._utils.normalizers import abi_address_to_hex, abi_bytes_to_bytes, abi_ens_resolver, abi_string_to_text
from web3.exceptions import BlockNumberOutofRange, Web3ValidationError
from web3.types import ABI, ABIEvent, ABIFunction, BlockIdentifier, BlockNumber, TxParams
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3


def extract_argument_types(*args: Sequence[Any]) ->str:
    """
    Takes a list of arguments and returns a string representation of the argument types,
    appropriately collapsing `tuple` types into the respective nested types.
    """
    def get_type(arg):
        if isinstance(arg, tuple):
            return f"({','.join(get_type(a) for a in arg)})"
        elif isinstance(arg, list):
            return f"{get_type(arg[0]) if arg else 'unknown'}[]"
        elif isinstance(arg, int):
            return "uint256"  # Assuming uint256 for integers
        elif isinstance(arg, bool):
            return "bool"
        elif isinstance(arg, str):
            return "string"
        elif isinstance(arg, bytes):
            return "bytes"
        else:
            return "unknown"
    
    return ",".join(get_type(arg) for arg in args)


def prepare_transaction(address: ChecksumAddress, w3: Union['AsyncWeb3',
    'Web3'], fn_identifier: Union[str, Type[FallbackFn], Type[ReceiveFn]],
    contract_abi: Optional[ABI]=None, fn_abi: Optional[ABIFunction]=None,
    transaction: Optional[TxParams]=None, fn_args: Optional[Sequence[Any]]=
    None, fn_kwargs: Optional[Any]=None) ->TxParams:
    """
    :parameter `is_function_abi` is used to distinguish  function abi from contract abi
    Returns a dictionary of the transaction that could be used to call this
    TODO: make this a public API
    TODO: add new prepare_deploy_transaction API
    """
    if transaction is None:
        transaction = {}
    
    if fn_identifier is FallbackFn:
        fn_abi = get_fallback_func_abi(contract_abi)
    elif fn_identifier is ReceiveFn:
        fn_abi = get_receive_func_abi(contract_abi)
    elif not is_text(fn_identifier):
        raise TypeError("Unsupported function identifier")
    elif fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, fn_identifier, fn_args, fn_kwargs)
    
    validate_payable(transaction, fn_abi)

    if transaction.get('data'):
        raise ValueError("Transaction parameter may not contain a 'data' key")

    if transaction.get('to') and transaction['to'] != address:
        raise ValueError("Supplied 'to' address in transaction does not match the contract address")

    if 'to' not in transaction:
        transaction['to'] = address

    if 'value' not in transaction:
        transaction['value'] = 0

    if fn_identifier is FallbackFn:
        transaction['data'] = '0x'
    elif fn_identifier is ReceiveFn:
        transaction['data'] = '0x'
    else:
        transaction['data'] = encode_transaction_data(
            w3,
            fn_identifier,
            contract_abi,
            fn_abi,
            fn_args,
            fn_kwargs,
        )

    return transaction


def validate_payable(transaction: TxParams, abi: ABIFunction) ->None:
    """Raise Web3ValidationError if non-zero ether
    is sent to a non-payable function.
    """
    if 'value' in transaction:
        if transaction['value'] != 0:
            if "payable" not in abi.get('stateMutability', '') and not abi.get('payable', False):
                raise Web3ValidationError(
                    "Sending non-zero ether to a non-payable function"
                )
