from functools import singledispatch
import operator
from typing import TYPE_CHECKING, Any, Callable, Collection, Iterable, Tuple, TypeVar, Union
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_keys.datatypes import PrivateKey
from eth_typing import ChecksumAddress, HexStr
from eth_utils import to_checksum_address, to_dict
from eth_utils.curried import apply_formatter_if
from eth_utils.toolz import compose
from web3._utils.async_transactions import async_fill_nonce, async_fill_transaction_defaults
from web3._utils.method_formatters import STANDARD_NORMALIZERS
from web3._utils.rpc_abi import TRANSACTION_PARAMS_ABIS, apply_abi_formatters_to_dict
from web3._utils.transactions import fill_nonce, fill_transaction_defaults
from web3.types import AsyncMiddleware, AsyncMiddlewareCoroutine, Middleware, RPCEndpoint, RPCResponse, TxParams
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3
T = TypeVar('T')
to_hexstr_from_eth_key = operator.methodcaller('to_hex')
key_normalizer = compose(apply_formatter_if(is_eth_key, to_hexstr_from_eth_key)
    )
_PrivateKey = Union[LocalAccount, PrivateKey, HexStr, bytes]
to_account.register(PrivateKey, private_key_to_account)
to_account.register(str, private_key_to_account)
to_account.register(bytes, private_key_to_account)


def format_transaction(transaction: TxParams) ->TxParams:
    """Format transaction so that it can be used correctly in the signing middleware.

    Converts bytes to hex strings and other types that can be passed to
    the underlying layers. Also has the effect of normalizing 'from' for
    easier comparisons.
    """
    formatted_transaction = apply_abi_formatters_to_dict(TRANSACTION_PARAMS_ABIS, transaction)
    if 'from' in formatted_transaction:
        formatted_transaction['from'] = to_checksum_address(formatted_transaction['from'])
    return formatted_transaction


def construct_sign_and_send_raw_middleware(private_key_or_account: Union[
    _PrivateKey, Collection[_PrivateKey]]) ->Middleware:
    """Capture transactions sign and send as raw transactions


    Keyword arguments:
    private_key_or_account -- A single private key or a tuple,
    list or set of private keys. Keys can be any of the following formats:
      - An eth_account.LocalAccount object
      - An eth_keys.PrivateKey object
      - A raw private key as a hex string or byte string
    """
    if isinstance(private_key_or_account, (list, tuple, set)):
        accounts = [to_account(pk) for pk in private_key_or_account]
    else:
        accounts = [to_account(private_key_or_account)]

    def middleware(make_request: Callable[[RPCEndpoint, Any], Any], w3: "Web3") -> Callable[[RPCEndpoint, Any], RPCResponse]:
        def middleware_fn(method: RPCEndpoint, params: Any) -> RPCResponse:
            if method != "eth_sendTransaction":
                return make_request(method, params)
            
            transaction = format_transaction(params[0])
            if 'from' not in transaction:
                return make_request(method, params)
            
            from_address = transaction['from']
            account = next((acct for acct in accounts if acct.address == from_address), None)
            if account is None:
                return make_request(method, params)

            transaction = fill_transaction_defaults(w3, transaction)
            transaction = fill_nonce(w3, transaction)
            signed = account.sign_transaction(transaction)
            return make_request("eth_sendRawTransaction", [signed.rawTransaction])

        return middleware_fn
    return middleware


async def async_construct_sign_and_send_raw_middleware(private_key_or_account:
    Union[_PrivateKey, Collection[_PrivateKey]]) ->AsyncMiddleware:
    """
    Capture transactions & sign and send as raw transactions

    Keyword arguments:
    private_key_or_account -- A single private key or a tuple,
    list or set of private keys. Keys can be any of the following formats:
      - An eth_account.LocalAccount object
      - An eth_keys.PrivateKey object
      - A raw private key as a hex string or byte string
    """
    if isinstance(private_key_or_account, (list, tuple, set)):
        accounts = [to_account(pk) for pk in private_key_or_account]
    else:
        accounts = [to_account(private_key_or_account)]

    async def middleware(make_request: Callable[[RPCEndpoint, Any], Any], w3: "AsyncWeb3") -> AsyncMiddlewareCoroutine:
        async def middleware_fn(method: RPCEndpoint, params: Any) -> RPCResponse:
            if method != "eth_sendTransaction":
                return await make_request(method, params)
            
            transaction = format_transaction(params[0])
            if 'from' not in transaction:
                return await make_request(method, params)
            
            from_address = transaction['from']
            account = next((acct for acct in accounts if acct.address == from_address), None)
            if account is None:
                return await make_request(method, params)

            transaction = await async_fill_transaction_defaults(w3, transaction)
            transaction = await async_fill_nonce(w3, transaction)
            signed = account.sign_transaction(transaction)
            return await make_request("eth_sendRawTransaction", [signed.rawTransaction])

        return middleware_fn
    return middleware
