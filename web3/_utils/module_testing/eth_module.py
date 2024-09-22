import json
import math
import pytest
from random import randint
import re
from typing import TYPE_CHECKING, Any, Callable, List, Union, cast
import eth_abi as abi
from eth_typing import BlockNumber, ChecksumAddress, HexAddress, HexStr
from eth_utils import is_boolean, is_bytes, is_checksum_address, is_dict, is_integer, is_list_like, is_same_address, is_string, remove_0x_prefix, to_bytes
from eth_utils.toolz import assoc
from hexbytes import HexBytes
from web3._utils.empty import empty
from web3._utils.ens import ens_addresses
from web3._utils.error_formatters_utils import PANIC_ERROR_CODES
from web3._utils.method_formatters import to_hex_if_integer
from web3._utils.module_testing.module_testing_utils import assert_contains_log, async_mock_offchain_lookup_request_response, flaky_geth_dev_mining, mock_offchain_lookup_request_response
from web3._utils.type_conversion import to_hex_if_bytes
from web3.exceptions import BlockNotFound, ContractCustomError, ContractLogicError, ContractPanicError, InvalidAddress, InvalidTransaction, MultipleFailedRequests, NameNotFound, OffchainLookup, TimeExhausted, TooManyRequests, TransactionNotFound, TransactionTypeMismatch, Web3ValidationError
from web3.middleware import async_geth_poa_middleware
from web3.middleware.fixture import async_construct_error_generator_middleware, async_construct_result_generator_middleware, construct_error_generator_middleware
from web3.types import ENS, BlockData, CallOverrideParams, FilterParams, Nonce, RPCEndpoint, SyncStatus, TxData, TxParams, Wei
UNKNOWN_ADDRESS = ChecksumAddress(HexAddress(HexStr(
    '0xdEADBEeF00000000000000000000000000000000')))
UNKNOWN_HASH = HexStr(
    '0xdeadbeef00000000000000000000000000000000000000000000000000000000')
OFFCHAIN_LOOKUP_TEST_DATA = (
    '0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001474657374206f6666636861696e206c6f6f6b7570000000000000000000000000'
    )
OFFCHAIN_LOOKUP_4BYTE_DATA = '0x556f1830'
OFFCHAIN_LOOKUP_RETURN_DATA = (
    '00000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000001c0da96d05a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002400000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000002c68747470733a2f2f776562332e70792f676174657761792f7b73656e6465727d2f7b646174617d2e6a736f6e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002568747470733a2f2f776562332e70792f676174657761792f7b73656e6465727d2e6a736f6e00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001474657374206f6666636861696e206c6f6f6b757000000000000000000000000000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001474657374206f6666636861696e206c6f6f6b7570000000000000000000000000'
    )
WEB3PY_AS_HEXBYTES = (
    '0x000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000067765623370790000000000000000000000000000000000000000000000000000'
    )
RLP_ACCESS_LIST = [('0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae', (
    '0x0000000000000000000000000000000000000000000000000000000000000003',
    '0x0000000000000000000000000000000000000000000000000000000000000007')),
    ('0xbb9bc244d798123fde783fcc1c72d3bb8c189413', ())]
RPC_ACCESS_LIST = [{'address': '0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae',
    'storageKeys': (
    '0x0000000000000000000000000000000000000000000000000000000000000003',
    '0x0000000000000000000000000000000000000000000000000000000000000007')},
    {'address': '0xbb9bc244d798123fde783fcc1c72d3bb8c189413', 'storageKeys':
    ()}]
if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
    from web3.contract import AsyncContract, Contract
    from web3.main import AsyncWeb3, Web3


class AsyncEthModuleTest:
    pass


class EthModuleTest:
    pass
