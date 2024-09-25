import math
from typing import TYPE_CHECKING, List, Optional, Union, cast
from eth_typing import ChecksumAddress
from eth_utils.toolz import assoc, curry, merge
from hexbytes import HexBytes
from web3._utils.compat import Literal
from web3._utils.utility_methods import all_in_dict, any_in_dict
from web3.constants import DYNAMIC_FEE_TXN_PARAMS
from web3.types import BlockIdentifier, TxData, TxParams, _Hash32
TX_PARAM_LITERALS = Literal['type', 'from', 'to', 'gas', 'maxFeePerGas',
    'maxPriorityFeePerGas', 'gasPrice', 'value', 'data', 'nonce', 'chainId',
    'accessList', 'maxFeePerBlobGas', 'blobVersionedHashes']
VALID_TRANSACTION_PARAMS: List[TX_PARAM_LITERALS] = ['type', 'from', 'to',
    'gas', 'accessList', 'maxFeePerGas', 'maxPriorityFeePerGas', 'gasPrice',
    'value', 'data', 'nonce', 'chainId', 'maxFeePerBlobGas',
    'blobVersionedHashes']
TRANSACTION_DEFAULTS = {'value': 0, 'data': b'', 'gas': lambda w3, tx: w3.
    eth.estimate_gas(tx), 'gasPrice': lambda w3, tx: w3.eth.
    generate_gas_price(tx), 'maxFeePerGas': lambda w3, tx: w3.eth.
    max_priority_fee + 2 * w3.eth.get_block('latest')['baseFeePerGas'],
    'maxPriorityFeePerGas': lambda w3, tx: w3.eth.max_priority_fee,
    'chainId': lambda w3, tx: w3.eth.chain_id}
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3


@curry
def fill_transaction_defaults(w3: 'Web3', transaction: TxParams) ->TxParams:
    """
    if w3 is None, fill as much as possible while offline
    """
    filled_transaction = cast(TxParams, {})

    if transaction.get('type') in DYNAMIC_FEE_TXN_PARAMS:
        # For dynamic fee transactions (EIP-1559)
        defaults = ['maxFeePerGas', 'maxPriorityFeePerGas', 'gas', 'value', 'data', 'chainId']
    else:
        # For legacy transactions
        defaults = ['gasPrice', 'gas', 'value', 'data', 'chainId']

    for key, default_val in TRANSACTION_DEFAULTS.items():
        if key in defaults:
            if key not in transaction:
                if callable(default_val):
                    if w3 is not None:
                        filled_transaction[key] = default_val(w3, transaction)
                else:
                    filled_transaction[key] = default_val

    filled_transaction = merge(filled_transaction, transaction)

    if 'gas' in filled_transaction and filled_transaction['gas'] is None:
        filled_transaction = assoc(filled_transaction, 'gas', w3.eth.estimate_gas(filled_transaction))

    return filled_transaction
