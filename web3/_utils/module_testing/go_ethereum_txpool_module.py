import pytest
from web3 import AsyncWeb3, Web3


class GoEthereumAsyncTxPoolModuleTest:
    @pytest.mark.asyncio
    async def test_txpool_content(self, async_w3: AsyncWeb3):
        content = await async_w3.txpool.content()
        assert isinstance(content, dict)
        assert all(key in content for key in ('pending', 'queued'))

    @pytest.mark.asyncio
    async def test_txpool_inspect(self, async_w3: AsyncWeb3):
        inspect = await async_w3.txpool.inspect()
        assert isinstance(inspect, dict)
        assert all(key in inspect for key in ('pending', 'queued'))

    @pytest.mark.asyncio
    async def test_txpool_status(self, async_w3: AsyncWeb3):
        status = await async_w3.txpool.status()
        assert isinstance(status, dict)
        assert all(key in status for key in ('pending', 'queued'))


class GoEthereumTxPoolModuleTest:
    def test_txpool_content(self, w3: Web3):
        content = w3.txpool.content()
        assert isinstance(content, dict)
        assert all(key in content for key in ('pending', 'queued'))

    def test_txpool_inspect(self, w3: Web3):
        inspect = w3.txpool.inspect()
        assert isinstance(inspect, dict)
        assert all(key in inspect for key in ('pending', 'queued'))

    def test_txpool_status(self, w3: Web3):
        status = w3.txpool.status()
        assert isinstance(status, dict)
        assert all(key in status for key in ('pending', 'queued'))
