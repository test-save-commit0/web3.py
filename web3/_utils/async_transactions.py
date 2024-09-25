from typing import TYPE_CHECKING, Optional, cast
from eth_typing import ChecksumAddress
from eth_utils.toolz import assoc, merge
from hexbytes import HexBytes
from web3._utils.transactions import prepare_replacement_transaction
from web3._utils.utility_methods import any_in_dict
from web3.constants import DYNAMIC_FEE_TXN_PARAMS
from web3.types import BlockIdentifier, TxData, TxParams, Wei, _Hash32
if TYPE_CHECKING:
    from web3.eth import AsyncEth
    from web3.main import AsyncWeb3
TRANSACTION_DEFAULTS = {'value': 0, 'data': b'', 'gas': _estimate_gas,
    'gasPrice': lambda async_w3, tx: async_w3.eth.generate_gas_price(tx),
    'maxFeePerGas': _max_fee_per_gas, 'maxPriorityFeePerGas':
    _max_priority_fee_gas, 'chainId': _chain_id}


async def async_fill_transaction_defaults(async_w3: 'AsyncWeb3',
    transaction: TxParams) ->TxParams:
    """
    if async_w3 is None, fill as much as possible while offline
    """
    filled_transaction = cast(TxParams, {})
    for key, default_getter in TRANSACTION_DEFAULTS.items():
        if key not in transaction:
            if callable(default_getter):
                if async_w3 is None:
                    continue
                default_val = (
                    await default_getter(async_w3, transaction)
                    if key in DYNAMIC_FEE_TXN_PARAMS
                    else await default_getter(async_w3, filled_transaction)
                )
            else:
                default_val = default_getter
            filled_transaction[key] = default_val
    
    filled_transaction = merge(filled_transaction, transaction)
    
    if async_w3 is not None:
        if 'from' not in filled_transaction:
            filled_transaction['from'] = await async_w3.eth.default_account
        
        if filled_transaction.get('nonce') is None:
            filled_transaction['nonce'] = await async_w3.eth.get_transaction_count(
                filled_transaction['from']
            )
        
        if 'chainId' not in filled_transaction:
            filled_transaction['chainId'] = await async_w3.eth.chain_id
    
    return filled_transaction
