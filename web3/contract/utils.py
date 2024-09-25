import itertools
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Sequence, Tuple, Type, Union
from eth_abi.exceptions import DecodingError
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3._utils.abi import filter_by_type, get_abi_output_types, map_abi_data, named_tree, recursive_dict_to_namedtuple
from web3._utils.async_transactions import async_fill_transaction_defaults
from web3._utils.contracts import find_matching_fn_abi, prepare_transaction
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS
from web3._utils.transactions import fill_transaction_defaults
from web3.exceptions import BadFunctionCallOutput
from web3.types import ABI, ABIFunction, BlockIdentifier, CallOverride, FunctionIdentifier, TContractFn, TxParams
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3
ACCEPTABLE_EMPTY_STRINGS = ['0x', b'0x', '', b'']


def call_contract_function(w3: 'Web3', address: ChecksumAddress,
    normalizers: Tuple[Callable[..., Any], ...], function_identifier:
    FunctionIdentifier, transaction: TxParams, block_id: Optional[
    BlockIdentifier]=None, contract_abi: Optional[ABI]=None, fn_abi:
    Optional[ABIFunction]=None, state_override: Optional[CallOverride]=None,
    ccip_read_enabled: Optional[bool]=None, decode_tuples: Optional[bool]=
    False, *args: Any, **kwargs: Any) ->Any:
    """
    Helper function for interacting with a contract function using the
    `eth_call` API.
    """
    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, function_identifier, args, kwargs)

    if transaction is None:
        transaction = {}

    processed_transaction = prepare_transaction(
        address,
        w3,
        fn_identifier=function_identifier,
        contract_abi=contract_abi,
        fn_abi=fn_abi,
        transaction=transaction,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    call_transaction = fill_transaction_defaults(w3, processed_transaction)

    output_types = get_abi_output_types(fn_abi)

    call_params = {
        'to': address,
        'data': call_transaction['data'],
    }
    if 'gas' in call_transaction:
        call_params['gas'] = call_transaction['gas']

    if state_override is not None:
        call_params['state_override'] = state_override

    if ccip_read_enabled is not None:
        call_params['ccip_read_enabled'] = ccip_read_enabled

    result = w3.eth.call(call_params, block_identifier=block_id)

    try:
        output_data = w3.codec.decode(output_types, result)
    except DecodingError as e:
        # Provide a more helpful error message than the one provided by
        # eth-abi-utils
        msg = (
            "Could not decode contract function call {} return data {} for "
            "output_types {}".format(
                function_identifier,
                result,
                output_types
            )
        )
        raise BadFunctionCallOutput(msg) from e

    normalized_data = map_abi_data(normalizers, output_types, output_data)

    if len(normalized_data) == 1:
        return normalized_data[0]
    elif decode_tuples:
        return named_tree(normalized_data, output_types)
    else:
        return normalized_data


def transact_with_contract_function(address: ChecksumAddress, w3: 'Web3',
    function_name: Optional[FunctionIdentifier]=None, transaction: Optional
    [TxParams]=None, contract_abi: Optional[ABI]=None, fn_abi: Optional[
    ABIFunction]=None, *args: Any, **kwargs: Any) ->HexBytes:
    """
    Helper function for interacting with a contract function by sending a
    transaction.
    """
    if transaction is None:
        transaction = {}

    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, function_name, args, kwargs)

    if function_name is None:
        function_name = fn_abi['name']

    processed_transaction = prepare_transaction(
        address,
        w3,
        fn_identifier=function_name,
        contract_abi=contract_abi,
        transaction=transaction,
        fn_abi=fn_abi,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    txn_hash = w3.eth.send_transaction(processed_transaction)
    return txn_hash


def estimate_gas_for_function(address: ChecksumAddress, w3: 'Web3',
    fn_identifier: Optional[FunctionIdentifier]=None, transaction: Optional
    [TxParams]=None, contract_abi: Optional[ABI]=None, fn_abi: Optional[
    ABIFunction]=None, block_identifier: Optional[BlockIdentifier]=None,
    state_override: Optional[CallOverride]=None, *args: Any, **kwargs: Any
    ) ->int:
    """Estimates gas cost a function call would take.

    Don't call this directly, instead use :meth:`Contract.estimate_gas`
    on your contract instance.
    """
    if transaction is None:
        transaction = {}

    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, fn_identifier, args, kwargs)

    if fn_identifier is None:
        fn_identifier = fn_abi['name']

    processed_transaction = prepare_transaction(
        address,
        w3,
        fn_identifier=fn_identifier,
        contract_abi=contract_abi,
        fn_abi=fn_abi,
        transaction=transaction,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    gas_estimate = w3.eth.estimate_gas(
        processed_transaction,
        block_identifier=block_identifier,
        state_override=state_override
    )

    return gas_estimate


def build_transaction_for_function(address: ChecksumAddress, w3: 'Web3',
    function_name: Optional[FunctionIdentifier]=None, transaction: Optional
    [TxParams]=None, contract_abi: Optional[ABI]=None, fn_abi: Optional[
    ABIFunction]=None, *args: Any, **kwargs: Any) ->TxParams:
    """Builds a dictionary with the fields required to make the given transaction

    Don't call this directly, instead use :meth:`Contract.build_transaction`
    on your contract instance.
    """
    if transaction is None:
        transaction = {}

    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, function_name, args, kwargs)

    if function_name is None:
        function_name = fn_abi['name']

    processed_transaction = prepare_transaction(
        address,
        w3,
        fn_identifier=function_name,
        contract_abi=contract_abi,
        transaction=transaction,
        fn_abi=fn_abi,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    return fill_transaction_defaults(w3, processed_transaction)


async def async_call_contract_function(async_w3: 'AsyncWeb3', address:
    ChecksumAddress, normalizers: Tuple[Callable[..., Any], ...],
    function_identifier: FunctionIdentifier, transaction: TxParams,
    block_id: Optional[BlockIdentifier]=None, contract_abi: Optional[ABI]=
    None, fn_abi: Optional[ABIFunction]=None, state_override: Optional[
    CallOverride]=None, ccip_read_enabled: Optional[bool]=None,
    decode_tuples: Optional[bool]=False, *args: Any, **kwargs: Any) ->Any:
    """
    Helper function for interacting with a contract function using the
    `eth_call` API.
    """
    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, function_identifier, args, kwargs)

    if transaction is None:
        transaction = {}

    processed_transaction = prepare_transaction(
        address,
        async_w3,
        fn_identifier=function_identifier,
        contract_abi=contract_abi,
        fn_abi=fn_abi,
        transaction=transaction,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    call_transaction = await async_fill_transaction_defaults(async_w3, processed_transaction)

    output_types = get_abi_output_types(fn_abi)

    call_params = {
        'to': address,
        'data': call_transaction['data'],
    }
    if 'gas' in call_transaction:
        call_params['gas'] = call_transaction['gas']

    if state_override is not None:
        call_params['state_override'] = state_override

    if ccip_read_enabled is not None:
        call_params['ccip_read_enabled'] = ccip_read_enabled

    result = await async_w3.eth.call(call_params, block_identifier=block_id)

    try:
        output_data = async_w3.codec.decode(output_types, result)
    except DecodingError as e:
        msg = (
            "Could not decode contract function call {} return data {} for "
            "output_types {}".format(
                function_identifier,
                result,
                output_types
            )
        )
        raise BadFunctionCallOutput(msg) from e

    normalized_data = map_abi_data(normalizers, output_types, output_data)

    if len(normalized_data) == 1:
        return normalized_data[0]
    elif decode_tuples:
        return named_tree(normalized_data, output_types)
    else:
        return normalized_data


async def async_transact_with_contract_function(address: ChecksumAddress,
    async_w3: 'AsyncWeb3', function_name: Optional[FunctionIdentifier]=None,
    transaction: Optional[TxParams]=None, contract_abi: Optional[ABI]=None,
    fn_abi: Optional[ABIFunction]=None, *args: Any, **kwargs: Any) ->HexBytes:
    """
    Helper function for interacting with a contract function by sending a
    transaction.
    """
    if transaction is None:
        transaction = {}

    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, function_name, args, kwargs)

    if function_name is None:
        function_name = fn_abi['name']

    processed_transaction = prepare_transaction(
        address,
        async_w3,
        fn_identifier=function_name,
        contract_abi=contract_abi,
        transaction=transaction,
        fn_abi=fn_abi,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    txn_hash = await async_w3.eth.send_transaction(processed_transaction)
    return txn_hash


async def async_estimate_gas_for_function(address: ChecksumAddress,
    async_w3: 'AsyncWeb3', fn_identifier: Optional[FunctionIdentifier]=None,
    transaction: Optional[TxParams]=None, contract_abi: Optional[ABI]=None,
    fn_abi: Optional[ABIFunction]=None, block_identifier: Optional[
    BlockIdentifier]=None, state_override: Optional[CallOverride]=None, *
    args: Any, **kwargs: Any) ->int:
    """Estimates gas cost a function call would take.

    Don't call this directly, instead use :meth:`Contract.estimate_gas`
    on your contract instance.
    """
    if transaction is None:
        transaction = {}

    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, fn_identifier, args, kwargs)

    if fn_identifier is None:
        fn_identifier = fn_abi['name']

    processed_transaction = prepare_transaction(
        address,
        async_w3,
        fn_identifier=fn_identifier,
        contract_abi=contract_abi,
        fn_abi=fn_abi,
        transaction=transaction,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    gas_estimate = await async_w3.eth.estimate_gas(
        processed_transaction,
        block_identifier=block_identifier,
        state_override=state_override
    )

    return gas_estimate


async def async_build_transaction_for_function(address: ChecksumAddress,
    async_w3: 'AsyncWeb3', function_name: Optional[FunctionIdentifier]=None,
    transaction: Optional[TxParams]=None, contract_abi: Optional[ABI]=None,
    fn_abi: Optional[ABIFunction]=None, *args: Any, **kwargs: Any) ->TxParams:
    """Builds a dictionary with the fields required to make the given transaction

    Don't call this directly, instead use :meth:`Contract.build_transaction`
    on your contract instance.
    """
    if transaction is None:
        transaction = {}

    if fn_abi is None:
        fn_abi = find_matching_fn_abi(contract_abi, function_name, args, kwargs)

    if function_name is None:
        function_name = fn_abi['name']

    processed_transaction = prepare_transaction(
        address,
        async_w3,
        fn_identifier=function_name,
        contract_abi=contract_abi,
        transaction=transaction,
        fn_abi=fn_abi,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    return await async_fill_transaction_defaults(async_w3, processed_transaction)
