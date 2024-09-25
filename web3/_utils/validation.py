import itertools
from typing import Any, Dict
from eth_typing import HexStr, TypeStr
from eth_utils import function_abi_to_4byte_selector, is_0x_prefixed, is_binary_address, is_boolean, is_bytes, is_checksum_address, is_dict, is_hex_address, is_integer, is_list_like, is_string
from eth_utils.curried import apply_formatter_to_array
from eth_utils.hexadecimal import encode_hex
from eth_utils.toolz import compose, groupby, valfilter, valmap
from ens.utils import is_valid_ens_name
from web3._utils.abi import abi_to_signature, filter_by_type, is_address_type, is_array_type, is_bool_type, is_bytes_type, is_int_type, is_recognized_type, is_string_type, is_uint_type, length_of_array_type, sub_type_of_array_type
from web3.exceptions import InvalidAddress

def is_address(value: Any) -> bool:
    """
    Check if the given value is a valid Ethereum address.
    """
    if not isinstance(value, str):
        return False
    if is_checksum_address(value):
        return True
    if is_hex_address(value):
        return True
    if is_binary_address(value):
        return True
    if is_valid_ens_name(value):
        return True
    return False
from web3.types import ABI, ABIFunction


def validate_abi(abi: ABI) ->None:
    """
    Helper function for validating an ABI
    """
    if not isinstance(abi, list):
        raise ValueError("ABI must be a list")
    for item in abi:
        if not isinstance(item, dict):
            raise ValueError("ABI items must be dictionaries")
        if "type" not in item:
            raise ValueError("ABI item must have a 'type' key")


def validate_abi_type(abi_type: TypeStr) ->None:
    """
    Helper function for validating an abi_type
    """
    if not is_recognized_type(abi_type):
        raise ValueError(f"Invalid ABI type: {abi_type}")


def validate_abi_value(abi_type: TypeStr, value: Any) ->None:
    """
    Helper function for validating a value against the expected abi_type
    Note: abi_type 'bytes' must either be python3 'bytes' object or ''
    """
    if is_array_type(abi_type):
        sub_type = sub_type_of_array_type(abi_type)
        if not is_list_like(value):
            raise ValueError(f"Expected list for array type: {abi_type}")
        for item in value:
            validate_abi_value(sub_type, item)
    elif is_bool_type(abi_type):
        if not is_boolean(value):
            raise ValueError(f"Expected boolean for type: {abi_type}")
    elif is_int_type(abi_type) or is_uint_type(abi_type):
        if not is_integer(value):
            raise ValueError(f"Expected integer for type: {abi_type}")
    elif is_address_type(abi_type):
        validate_address(value)
    elif is_bytes_type(abi_type):
        if not (is_bytes(value) or value == ''):
            raise ValueError(f"Expected bytes or empty string for type: {abi_type}")
    elif is_string_type(abi_type):
        if not is_string(value):
            raise ValueError(f"Expected string for type: {abi_type}")
    else:
        raise ValueError(f"Unsupported ABI type: {abi_type}")


def validate_address(value: Any) ->None:
    """
    Helper function for validating an address
    """
    if not is_address(value):
        raise InvalidAddress(f"'{value}' is not a valid address")
