import json
import pytest
from typing import TYPE_CHECKING, cast
from eth_typing import ChecksumAddress
from eth_utils import is_checksum_address, is_list_like, is_same_address, is_string
from hexbytes import HexBytes
from web3 import constants
from web3.datastructures import AttributeDict
from web3.types import TxParams, Wei
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3
PRIVATE_KEY_HEX = (
    '0x56ebb41875ceedd42e395f730e03b5c44989393c9f0484ee6bc05f933673458f')
SECOND_PRIVATE_KEY_HEX = (
    '0x56ebb41875ceedd42e395f730e03b5c44989393c9f0484ee6bc05f9336712345')
THIRD_PRIVATE_KEY_HEX = (
    '0x56ebb41875ceedd42e395f730e03b5c44989393c9f0484ee6bc05f9336754321')
PASSWORD = 'web3-testing'
ADDRESS = '0x844B417c0C58B02c2224306047B9fb0D3264fE8c'
SECOND_ADDRESS = '0xB96b6B21053e67BA59907E252D990C71742c41B8'
PRIVATE_KEY_FOR_UNLOCK = (
    '0x392f63a79b1ff8774845f3fa69de4a13800a59e7083f5187f1558f0797ad0f01')
ACCOUNT_FOR_UNLOCK = '0x12efDc31B1a8FA1A1e756DFD8A1601055C971E13'


class GoEthereumPersonalModuleTest:
    def test_personal_import_raw_key(self, web3: "Web3") -> None:
        actual = web3.geth.personal.import_raw_key(PRIVATE_KEY_HEX, PASSWORD)
        assert actual == ADDRESS

    def test_personal_list_accounts(self, web3: "Web3") -> None:
        accounts = web3.geth.personal.list_accounts()
        assert is_list_like(accounts)
        assert len(accounts) > 0
        assert all((is_checksum_address(item) for item in accounts))

    def test_personal_list_wallets(self, web3: "Web3") -> None:
        wallets = web3.geth.personal.list_wallets()
        assert is_list_like(wallets)
        assert len(wallets) > 0
        assert all((isinstance(item, AttributeDict) for item in wallets))
        assert all((is_checksum_address(item['accounts'][0]['address']) for item in wallets))

    def test_personal_lock_account(self, web3: "Web3") -> None:
        # Unlock the account first
        web3.geth.personal.unlock_account(ACCOUNT_FOR_UNLOCK, PASSWORD)
        # Now lock it
        result = web3.geth.personal.lock_account(ACCOUNT_FOR_UNLOCK)
        assert result is True

    def test_personal_new_account(self, web3: "Web3") -> None:
        new_account = web3.geth.personal.new_account(PASSWORD)
        assert is_checksum_address(new_account)

    def test_personal_send_transaction(self, web3: "Web3", unlockable_account_dual_type: ChecksumAddress) -> None:
        assert unlockable_account_dual_type.startswith('0x')

        tx_params: TxParams = {
            'from': unlockable_account_dual_type,
            'to': unlockable_account_dual_type,
            'value': Wei(1),
            'gas': 21000,
            'gasPrice': web3.eth.gas_price,
        }
        txn_hash = web3.geth.personal.send_transaction(tx_params, PASSWORD)
        assert txn_hash
        assert isinstance(txn_hash, HexBytes)

    def test_personal_sign_and_ecrecover(self, web3: "Web3", unlockable_account_dual_type: ChecksumAddress) -> None:
        message = 'test message'
        signature = web3.geth.personal.sign(message, unlockable_account_dual_type, PASSWORD)
        assert isinstance(signature, HexBytes)
        recovered = web3.geth.personal.ec_recover(message, signature)
        assert is_same_address(recovered, unlockable_account_dual_type)

    def test_personal_unlock_account(self, web3: "Web3") -> None:
        result = web3.geth.personal.unlock_account(ACCOUNT_FOR_UNLOCK, PASSWORD)
        assert result is True


class GoEthereumAsyncPersonalModuleTest:
    @pytest.mark.asyncio
    async def test_async_personal_import_raw_key(self, async_w3: "AsyncWeb3") -> None:
        actual = await async_w3.geth.personal.import_raw_key(PRIVATE_KEY_HEX, PASSWORD)
        assert actual == ADDRESS

    @pytest.mark.asyncio
    async def test_async_personal_list_accounts(self, async_w3: "AsyncWeb3") -> None:
        accounts = await async_w3.geth.personal.list_accounts()
        assert is_list_like(accounts)
        assert len(accounts) > 0
        assert all((is_checksum_address(item) for item in accounts))

    @pytest.mark.asyncio
    async def test_async_personal_list_wallets(self, async_w3: "AsyncWeb3") -> None:
        wallets = await async_w3.geth.personal.list_wallets()
        assert is_list_like(wallets)
        assert len(wallets) > 0
        assert all((isinstance(item, AttributeDict) for item in wallets))
        assert all((is_checksum_address(item['accounts'][0]['address']) for item in wallets))

    @pytest.mark.asyncio
    async def test_async_personal_lock_account(self, async_w3: "AsyncWeb3") -> None:
        # Unlock the account first
        await async_w3.geth.personal.unlock_account(ACCOUNT_FOR_UNLOCK, PASSWORD)
        # Now lock it
        result = await async_w3.geth.personal.lock_account(ACCOUNT_FOR_UNLOCK)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_personal_new_account(self, async_w3: "AsyncWeb3") -> None:
        new_account = await async_w3.geth.personal.new_account(PASSWORD)
        assert is_checksum_address(new_account)

    @pytest.mark.asyncio
    async def test_async_personal_send_transaction(self, async_w3: "AsyncWeb3", unlockable_account_dual_type: ChecksumAddress) -> None:
        assert unlockable_account_dual_type.startswith('0x')

        tx_params: TxParams = {
            'from': unlockable_account_dual_type,
            'to': unlockable_account_dual_type,
            'value': Wei(1),
            'gas': 21000,
            'gasPrice': await async_w3.eth.gas_price,
        }
        txn_hash = await async_w3.geth.personal.send_transaction(tx_params, PASSWORD)
        assert txn_hash
        assert isinstance(txn_hash, HexBytes)

    @pytest.mark.asyncio
    async def test_async_personal_sign_and_ecrecover(self, async_w3: "AsyncWeb3", unlockable_account_dual_type: ChecksumAddress) -> None:
        message = 'test message'
        signature = await async_w3.geth.personal.sign(message, unlockable_account_dual_type, PASSWORD)
        assert isinstance(signature, HexBytes)
        recovered = await async_w3.geth.personal.ec_recover(message, signature)
        assert is_same_address(recovered, unlockable_account_dual_type)

    @pytest.mark.asyncio
    async def test_async_personal_unlock_account(self, async_w3: "AsyncWeb3") -> None:
        result = await async_w3.geth.personal.unlock_account(ACCOUNT_FOR_UNLOCK, PASSWORD)
        assert result is True
