import ast
import operator
import random
import sys
from typing import TYPE_CHECKING, Any, Callable, List, NoReturn, Optional, Tuple, Type
from eth_abi import abi
from eth_tester.exceptions import BlockNotFound, FilterNotFound, TransactionFailed, TransactionNotFound, ValidationError
from eth_typing import HexAddress, HexStr
from eth_utils import decode_hex, encode_hex, is_null, keccak
from eth_utils.curried import apply_formatter_if
from eth_utils.toolz import compose, curry, excepts
from web3 import Web3
from web3._utils.error_formatters_utils import OFFCHAIN_LOOKUP_FIELDS, PANIC_ERROR_CODES
from web3.exceptions import ContractPanicError, OffchainLookup
from web3.types import LogReceipt, RPCResponse, TParams, TReturn, TValue, TxReceipt
if TYPE_CHECKING:
    from eth_tester import EthereumTester
null_if_block_not_found = null_if_excepts(BlockNotFound)
null_if_transaction_not_found = null_if_excepts(TransactionNotFound)
null_if_filter_not_found = null_if_excepts(FilterNotFound)
null_if_indexerror = null_if_excepts(IndexError)


def _generate_random_private_key() -> HexStr:
    """
    WARNING: This is not a secure way to generate private keys and should only
    be used for testing purposes.
    """
    private_key = '0x' + ''.join([random.choice('0123456789abcdef') for _ in range(64)])
    return HexStr(private_key)


API_ENDPOINTS = {'web3': {'clientVersion': client_version, 'sha3': compose(
    encode_hex, keccak, decode_hex, without_eth_tester(operator.itemgetter(
    0)))}, 'net': {'version': static_return('1'), 'listening':
    static_return(False), 'peerCount': static_return(0)}, 'eth': {
    'protocolVersion': static_return(63), 'syncing': static_return(False),
    'coinbase': compose(operator.itemgetter(0), call_eth_tester(
    'get_accounts')), 'mining': static_return(False), 'hashrate':
    static_return(0), 'chainId': static_return(131277322940537),
    'feeHistory': call_eth_tester('get_fee_history'),
    'maxPriorityFeePerGas': static_return(10 ** 9), 'gasPrice':
    static_return(10 ** 9), 'accounts': call_eth_tester('get_accounts'),
    'blockNumber': compose(operator.itemgetter('number'), call_eth_tester(
    'get_block_by_number', fn_kwargs={'block_number': 'latest'})),
    'getBalance': call_eth_tester('get_balance'), 'getStorageAt':
    call_eth_tester('get_storage_at'), 'getProof': not_implemented,
    'getTransactionCount': call_eth_tester('get_nonce'),
    'getBlockTransactionCountByHash': null_if_block_not_found(compose(len,
    operator.itemgetter('transactions'), call_eth_tester(
    'get_block_by_hash'))), 'getBlockTransactionCountByNumber':
    null_if_block_not_found(compose(len, operator.itemgetter('transactions'
    ), call_eth_tester('get_block_by_number'))), 'getUncleCountByBlockHash':
    null_if_block_not_found(compose(len, operator.itemgetter('uncles'),
    call_eth_tester('get_block_by_hash'))), 'getUncleCountByBlockNumber':
    null_if_block_not_found(compose(len, operator.itemgetter('uncles'),
    call_eth_tester('get_block_by_number'))), 'getCode': call_eth_tester(
    'get_code'), 'sign': not_implemented, 'signTransaction':
    not_implemented, 'sendTransaction': call_eth_tester('send_transaction'),
    'sendRawTransaction': call_eth_tester('send_raw_transaction'), 'call':
    call_eth_tester('call'), 'createAccessList': not_implemented,
    'estimateGas': call_eth_tester('estimate_gas'), 'getBlockByHash':
    null_if_block_not_found(call_eth_tester('get_block_by_hash')),
    'getBlockByNumber': null_if_block_not_found(call_eth_tester(
    'get_block_by_number')), 'getTransactionByHash':
    null_if_transaction_not_found(call_eth_tester('get_transaction_by_hash'
    )), 'getTransactionByBlockHashAndIndex':
    get_transaction_by_block_hash_and_index,
    'getTransactionByBlockNumberAndIndex':
    get_transaction_by_block_number_and_index, 'getTransactionReceipt':
    null_if_transaction_not_found(compose(apply_formatter_if(compose(
    is_null, operator.itemgetter('block_number')), static_return(None)),
    call_eth_tester('get_transaction_receipt'))),
    'getUncleByBlockHashAndIndex': not_implemented,
    'getUncleByBlockNumberAndIndex': not_implemented, 'getCompilers':
    not_implemented, 'compileLLL': not_implemented, 'compileSolidity':
    not_implemented, 'compileSerpent': not_implemented, 'newFilter':
    create_log_filter, 'newBlockFilter': call_eth_tester(
    'create_block_filter'), 'newPendingTransactionFilter': call_eth_tester(
    'create_pending_transaction_filter'), 'uninstallFilter': excepts(
    FilterNotFound, compose(is_null, call_eth_tester('delete_filter')),
    static_return(False)), 'getFilterChanges': null_if_filter_not_found(
    call_eth_tester('get_only_filter_changes')), 'getFilterLogs':
    null_if_filter_not_found(call_eth_tester('get_all_filter_logs')),
    'getLogs': get_logs, 'getWork': not_implemented, 'submitWork':
    not_implemented, 'submitHashrate': not_implemented}, 'db': {'putString':
    not_implemented, 'getString': not_implemented, 'putHex':
    not_implemented, 'getHex': not_implemented}, 'admin': {'add_peer':
    not_implemented, 'datadir': not_implemented, 'node_info':
    not_implemented, 'peers': not_implemented, 'start_http':
    not_implemented, 'start_ws': not_implemented, 'stop_http':
    not_implemented, 'stop_ws': not_implemented}, 'debug': {'backtraceAt':
    not_implemented, 'blockProfile': not_implemented, 'cpuProfile':
    not_implemented, 'dumpBlock': not_implemented, 'gtStats':
    not_implemented, 'getBlockRLP': not_implemented, 'goTrace':
    not_implemented, 'memStats': not_implemented, 'seedHashSign':
    not_implemented, 'setBlockProfileRate': not_implemented, 'setHead':
    not_implemented, 'stacks': not_implemented, 'startCPUProfile':
    not_implemented, 'startGoTrace': not_implemented, 'stopCPUProfile':
    not_implemented, 'stopGoTrace': not_implemented, 'traceBlock':
    not_implemented, 'traceBlockByNumber': not_implemented,
    'traceBlockByHash': not_implemented, 'traceBlockFromFile':
    not_implemented, 'traceTransaction': not_implemented, 'verbosity':
    not_implemented, 'vmodule': not_implemented, 'writeBlockProfile':
    not_implemented, 'writeMemProfile': not_implemented}, 'miner': {
    'make_dag': not_implemented, 'set_extra': not_implemented,
    'set_gas_price': not_implemented, 'start': not_implemented, 'stop':
    not_implemented, 'start_auto_dag': not_implemented, 'stop_auto_dag':
    not_implemented}, 'personal': {'ec_recover': not_implemented,
    'import_raw_key': call_eth_tester('add_account'), 'list_accounts':
    call_eth_tester('get_accounts'), 'list_wallets': not_implemented,
    'lock_account': excepts(ValidationError, compose(static_return(True),
    call_eth_tester('lock_account')), static_return(False)), 'new_account':
    create_new_account, 'unlock_account': excepts(ValidationError, compose(
    static_return(True), call_eth_tester('unlock_account')), static_return(
    False)), 'send_transaction': personal_send_transaction, 'sign':
    not_implemented, 'ecRecover': not_implemented, 'importRawKey':
    call_eth_tester('add_account'), 'listAccounts': call_eth_tester(
    'get_accounts'), 'lockAccount': excepts(ValidationError, compose(
    static_return(True), call_eth_tester('lock_account')), static_return(
    False)), 'newAccount': create_new_account, 'unlockAccount': excepts(
    ValidationError, compose(static_return(True), call_eth_tester(
    'unlock_account')), static_return(False)), 'sendTransaction':
    personal_send_transaction}, 'testing': {'timeTravel': call_eth_tester(
    'time_travel')}, 'txpool': {'content': not_implemented, 'inspect':
    not_implemented, 'status': not_implemented}, 'evm': {'mine':
    call_eth_tester('mine_blocks'), 'revert': call_eth_tester(
    'revert_to_snapshot'), 'snapshot': call_eth_tester('take_snapshot')}}
