from typing import TYPE_CHECKING, Any, Callable
from eth_utils.toolz import assoc
from web3._utils.method_formatters import to_hex_if_integer
from web3._utils.utility_methods import all_in_dict, any_in_dict, none_in_dict
from web3.constants import DYNAMIC_FEE_TXN_PARAMS
from web3.exceptions import InvalidTransaction, TransactionTypeMismatch
from web3.types import AsyncMiddlewareCoroutine, BlockData, RPCEndpoint, RPCResponse, TxParams, Wei
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3


def gas_price_strategy_middleware(make_request: Callable[[RPCEndpoint, Any],
    Any], w3: 'Web3') ->Callable[[RPCEndpoint, Any], RPCResponse]:
    """
    - Uses a gas price strategy if one is set. This is only supported
      for legacy transactions. It is recommended to send dynamic fee
      transactions (EIP-1559) whenever possible.

    - Validates transaction params against legacy and dynamic fee txn values.
    """
    def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
        if method != 'eth_sendTransaction':
            return make_request(method, params)

        transaction = params[0]
        
        # Validate transaction params
        if any_in_dict(DYNAMIC_FEE_TXN_PARAMS, transaction) and any_in_dict(['gasPrice'], transaction):
            raise TransactionTypeMismatch("You cannot use legacy and EIP-1559 transaction parameters at the same time")
        
        if none_in_dict(DYNAMIC_FEE_TXN_PARAMS, transaction) and 'gasPrice' not in transaction:
            if w3.eth.gas_price_strategy:
                gas_price_strategy = w3.eth.gas_price_strategy
                gas_price = gas_price_strategy(w3, transaction)
                transaction = assoc(transaction, 'gasPrice', gas_price)
            else:
                raise InvalidTransaction("Gas price strategy not set and gasPrice not provided")

        # Convert values to hex if they are integers
        for key in ['gasPrice', 'maxFeePerGas', 'maxPriorityFeePerGas']:
            if key in transaction:
                transaction[key] = to_hex_if_integer(transaction[key])

        return make_request(method, [transaction])

    return middleware


async def async_gas_price_strategy_middleware(make_request: Callable[[
    RPCEndpoint, Any], Any], async_w3: 'AsyncWeb3') ->AsyncMiddlewareCoroutine:
    """
    - Uses a gas price strategy if one is set. This is only supported for
      legacy transactions. It is recommended to send dynamic fee transactions
      (EIP-1559) whenever possible.

    - Validates transaction params against legacy and dynamic fee txn values.
    """
    async def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
        if method != 'eth_sendTransaction':
            return await make_request(method, params)

        transaction = params[0]
        
        # Validate transaction params
        if any_in_dict(DYNAMIC_FEE_TXN_PARAMS, transaction) and any_in_dict(['gasPrice'], transaction):
            raise TransactionTypeMismatch("You cannot use legacy and EIP-1559 transaction parameters at the same time")
        
        if none_in_dict(DYNAMIC_FEE_TXN_PARAMS, transaction) and 'gasPrice' not in transaction:
            if async_w3.eth.gas_price_strategy:
                gas_price_strategy = async_w3.eth.gas_price_strategy
                gas_price = await gas_price_strategy(async_w3, transaction)
                transaction = assoc(transaction, 'gasPrice', gas_price)
            else:
                raise InvalidTransaction("Gas price strategy not set and gasPrice not provided")

        # Convert values to hex if they are integers
        for key in ['gasPrice', 'maxFeePerGas', 'maxPriorityFeePerGas']:
            if key in transaction:
                transaction[key] = to_hex_if_integer(transaction[key])

        return await make_request(method, [transaction])

    return middleware
