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
    async def test_eth_gas_price(self, async_w3: "AsyncWeb3") -> None:
        gas_price = await async_w3.eth.gas_price
        assert is_integer(gas_price)
        assert gas_price > 0

    async def test_eth_max_priority_fee(self, async_w3: "AsyncWeb3") -> None:
        max_priority_fee = await async_w3.eth.max_priority_fee
        assert is_integer(max_priority_fee)
        assert max_priority_fee > 0

    async def test_eth_accounts(self, async_w3: "AsyncWeb3") -> None:
        accounts = await async_w3.eth.accounts
        assert is_list_like(accounts)
        assert len(accounts) != 0
        assert all(is_checksum_address(account) for account in accounts)

    async def test_eth_block_number(self, async_w3: "AsyncWeb3") -> None:
        block_number = await async_w3.eth.block_number
        assert is_integer(block_number)
        assert block_number >= 0

    async def test_eth_get_block_number(self, async_w3: "AsyncWeb3") -> None:
        block_number = await async_w3.eth.get_block_number()
        assert is_integer(block_number)
        assert block_number >= 0

    async def test_eth_get_balance(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        balance = await async_w3.eth.get_balance(coinbase)
        assert is_integer(balance)
        assert balance >= 0

    async def test_eth_get_storage_at(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        storage = await async_w3.eth.get_storage_at(coinbase, 0)
        assert isinstance(storage, HexBytes)

    async def test_eth_get_transaction_count(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        transaction_count = await async_w3.eth.get_transaction_count(coinbase)
        assert is_integer(transaction_count)
        assert transaction_count >= 0

    async def test_eth_get_block(self, async_w3: "AsyncWeb3") -> None:
        latest_block = await async_w3.eth.get_block('latest')
        assert isinstance(latest_block, BlockData)
        assert latest_block['number'] > 0

    async def test_eth_get_code(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        code = await async_w3.eth.get_code(coinbase)
        assert isinstance(code, HexBytes)

    async def test_eth_sign(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        signature = await async_w3.eth.sign(coinbase, text='Hello World')
        assert isinstance(signature, HexBytes)
        assert len(signature) == 65

    async def test_eth_send_transaction(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        transaction = {
            'to': UNKNOWN_ADDRESS,
            'from': coinbase,
            'value': 1,
        }
        tx_hash = await async_w3.eth.send_transaction(transaction)
        assert isinstance(tx_hash, HexBytes)

    async def test_eth_get_transaction(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        transaction = {
            'to': UNKNOWN_ADDRESS,
            'from': coinbase,
            'value': 1,
        }
        tx_hash = await async_w3.eth.send_transaction(transaction)
        tx = await async_w3.eth.get_transaction(tx_hash)
        assert isinstance(tx, TxData)
        assert tx['hash'] == tx_hash

    async def test_eth_get_transaction_receipt(self, async_w3: "AsyncWeb3") -> None:
        coinbase = await async_w3.eth.coinbase
        transaction = {
            'to': UNKNOWN_ADDRESS,
            'from': coinbase,
            'value': 1,
        }
        tx_hash = await async_w3.eth.send_transaction(transaction)
        receipt = await async_w3.eth.wait_for_transaction_receipt(tx_hash)
        assert isinstance(receipt, TxData)
        assert receipt['transactionHash'] == tx_hash

    async def test_eth_get_transaction_receipt_unmined(self, async_w3: "AsyncWeb3") -> None:
        with pytest.raises(TransactionNotFound):
            await async_w3.eth.get_transaction_receipt(UNKNOWN_HASH)

    async def test_eth_get_transaction_by_block(self, async_w3: "AsyncWeb3") -> None:
        block = await async_w3.eth.get_block('latest')
        if len(block['transactions']) > 0:
            transaction = await async_w3.eth.get_transaction_by_block(block['number'], 0)
            assert isinstance(transaction, TxData)

    async def test_eth_get_uncle_by_block(self, async_w3: "AsyncWeb3") -> None:
        block = await async_w3.eth.get_block('latest')
        if len(block['uncles']) > 0:
            uncle = await async_w3.eth.get_uncle_by_block(block['number'], 0)
            assert isinstance(uncle, BlockData)

    async def test_eth_get_compilers(self, async_w3: "AsyncWeb3") -> None:
        compilers = await async_w3.eth.get_compilers()
        assert is_list_like(compilers)

    async def test_eth_syncing(self, async_w3: "AsyncWeb3") -> None:
        syncing = await async_w3.eth.syncing
        assert is_boolean(syncing) or isinstance(syncing, SyncStatus)

    async def test_eth_mining(self, async_w3: "AsyncWeb3") -> None:
        mining = await async_w3.eth.mining
        assert is_boolean(mining)

    async def test_eth_hashrate(self, async_w3: "AsyncWeb3") -> None:
        hashrate = await async_w3.eth.hashrate
        assert is_integer(hashrate)
        assert hashrate >= 0

    async def test_eth_chain_id(self, async_w3: "AsyncWeb3") -> None:
        chain_id = await async_w3.eth.chain_id
        assert is_integer(chain_id)
        assert chain_id > 0


class EthModuleTest:
    def test_eth_gas_price(self, web3: "Web3") -> None:
        gas_price = web3.eth.gas_price
        assert is_integer(gas_price)
        assert gas_price > 0

    def test_eth_max_priority_fee(self, web3: "Web3") -> None:
        max_priority_fee = web3.eth.max_priority_fee
        assert is_integer(max_priority_fee)
        assert max_priority_fee > 0

    def test_eth_accounts(self, web3: "Web3") -> None:
        accounts = web3.eth.accounts
        assert is_list_like(accounts)
        assert len(accounts) != 0
        assert all(is_checksum_address(account) for account in accounts)

    def test_eth_block_number(self, web3: "Web3") -> None:
        block_number = web3.eth.block_number
        assert is_integer(block_number)
        assert block_number >= 0

    def test_eth_get_block_number(self, web3: "Web3") -> None:
        block_number = web3.eth.get_block_number()
        assert is_integer(block_number)
        assert block_number >= 0

    def test_eth_get_balance(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        balance = web3.eth.get_balance(coinbase)
        assert is_integer(balance)
        assert balance >= 0

    def test_eth_get_storage_at(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        storage = web3.eth.get_storage_at(coinbase, 0)
        assert isinstance(storage, HexBytes)

    def test_eth_get_transaction_count(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        transaction_count = web3.eth.get_transaction_count(coinbase)
        assert is_integer(transaction_count)
        assert transaction_count >= 0

    def test_eth_get_block(self, web3: "Web3") -> None:
        latest_block = web3.eth.get_block('latest')
        assert isinstance(latest_block, BlockData)
        assert latest_block['number'] > 0

    def test_eth_get_code(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        code = web3.eth.get_code(coinbase)
        assert isinstance(code, HexBytes)

    def test_eth_sign(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        signature = web3.eth.sign(coinbase, text='Hello World')
        assert isinstance(signature, HexBytes)
        assert len(signature) == 65

    def test_eth_send_transaction(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        transaction = {
            'to': UNKNOWN_ADDRESS,
            'from': coinbase,
            'value': 1,
        }
        tx_hash = web3.eth.send_transaction(transaction)
        assert isinstance(tx_hash, HexBytes)

    def test_eth_get_transaction(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        transaction = {
            'to': UNKNOWN_ADDRESS,
            'from': coinbase,
            'value': 1,
        }
        tx_hash = web3.eth.send_transaction(transaction)
        tx = web3.eth.get_transaction(tx_hash)
        assert isinstance(tx, TxData)
        assert tx['hash'] == tx_hash

    def test_eth_get_transaction_receipt(self, web3: "Web3") -> None:
        coinbase = web3.eth.coinbase
        transaction = {
            'to': UNKNOWN_ADDRESS,
            'from': coinbase,
            'value': 1,
        }
        tx_hash = web3.eth.send_transaction(transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        assert isinstance(receipt, TxData)
        assert receipt['transactionHash'] == tx_hash

    def test_eth_get_transaction_receipt_unmined(self, web3: "Web3") -> None:
        with pytest.raises(TransactionNotFound):
            web3.eth.get_transaction_receipt(UNKNOWN_HASH)

    def test_eth_get_transaction_by_block(self, web3: "Web3") -> None:
        block = web3.eth.get_block('latest')
        if len(block['transactions']) > 0:
            transaction = web3.eth.get_transaction_by_block(block['number'], 0)
            assert isinstance(transaction, TxData)

    def test_eth_get_uncle_by_block(self, web3: "Web3") -> None:
        block = web3.eth.get_block('latest')
        if len(block['uncles']) > 0:
            uncle = web3.eth.get_uncle_by_block(block['number'], 0)
            assert isinstance(uncle, BlockData)

    def test_eth_get_compilers(self, web3: "Web3") -> None:
        compilers = web3.eth.get_compilers()
        assert is_list_like(compilers)

    def test_eth_syncing(self, web3: "Web3") -> None:
        syncing = web3.eth.syncing
        assert is_boolean(syncing) or isinstance(syncing, SyncStatus)

    def test_eth_mining(self, web3: "Web3") -> None:
        mining = web3.eth.mining
        assert is_boolean(mining)

    def test_eth_hashrate(self, web3: "Web3") -> None:
        hashrate = web3.eth.hashrate
        assert is_integer(hashrate)
        assert hashrate >= 0

    def test_eth_chain_id(self, web3: "Web3") -> None:
        chain_id = web3.eth.chain_id
        assert is_integer(chain_id)
        assert chain_id > 0
