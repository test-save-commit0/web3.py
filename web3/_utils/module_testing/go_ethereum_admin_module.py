import pytest
from typing import TYPE_CHECKING, List
from web3.datastructures import AttributeDict
from web3.types import EnodeURI
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3


class GoEthereumAdminModuleTest:
    def test_add_peer(self, w3: "Web3") -> None:
        enode = "enode://f1a6b0bdbf014355587c3018454d070ac57801f05d3b39fe85da574f002a32e929f683d72aa5a8318382e4d3c7a05c9b91687b0d997a39619fb8a6e7ad88e512@1.1.1.1:30303"
        result = w3.geth.admin.add_peer(enode)
        assert result

    def test_datadir(self, w3: "Web3") -> None:
        datadir = w3.geth.admin.datadir()
        assert isinstance(datadir, str)
        assert len(datadir) > 0

    def test_node_info(self, w3: "Web3") -> None:
        node_info = w3.geth.admin.node_info()
        assert isinstance(node_info, AttributeDict)
        assert 'enode' in node_info
        assert 'id' in node_info
        assert 'ip' in node_info
        assert 'listenAddr' in node_info
        assert 'name' in node_info

    def test_peers(self, w3: "Web3") -> None:
        peers = w3.geth.admin.peers()
        assert isinstance(peers, List)

    def test_start_rpc(self, w3: "Web3") -> None:
        result = w3.geth.admin.start_rpc()
        assert result

    def test_start_ws(self, w3: "Web3") -> None:
        result = w3.geth.admin.start_ws()
        assert result

    def test_stop_rpc(self, w3: "Web3") -> None:
        result = w3.geth.admin.stop_rpc()
        assert result

    def test_stop_ws(self, w3: "Web3") -> None:
        result = w3.geth.admin.stop_ws()
        assert result


class GoEthereumAsyncAdminModuleTest:
    @pytest.mark.asyncio
    async def test_add_peer(self, async_w3: "AsyncWeb3") -> None:
        enode = "enode://f1a6b0bdbf014355587c3018454d070ac57801f05d3b39fe85da574f002a32e929f683d72aa5a8318382e4d3c7a05c9b91687b0d997a39619fb8a6e7ad88e512@1.1.1.1:30303"
        result = await async_w3.geth.admin.add_peer(enode)
        assert result

    @pytest.mark.asyncio
    async def test_datadir(self, async_w3: "AsyncWeb3") -> None:
        datadir = await async_w3.geth.admin.datadir()
        assert isinstance(datadir, str)
        assert len(datadir) > 0

    @pytest.mark.asyncio
    async def test_node_info(self, async_w3: "AsyncWeb3") -> None:
        node_info = await async_w3.geth.admin.node_info()
        assert isinstance(node_info, AttributeDict)
        assert 'enode' in node_info
        assert 'id' in node_info
        assert 'ip' in node_info
        assert 'listenAddr' in node_info
        assert 'name' in node_info

    @pytest.mark.asyncio
    async def test_peers(self, async_w3: "AsyncWeb3") -> None:
        peers = await async_w3.geth.admin.peers()
        assert isinstance(peers, List)

    @pytest.mark.asyncio
    async def test_start_rpc(self, async_w3: "AsyncWeb3") -> None:
        result = await async_w3.geth.admin.start_rpc()
        assert result

    @pytest.mark.asyncio
    async def test_start_ws(self, async_w3: "AsyncWeb3") -> None:
        result = await async_w3.geth.admin.start_ws()
        assert result

    @pytest.mark.asyncio
    async def test_stop_rpc(self, async_w3: "AsyncWeb3") -> None:
        result = await async_w3.geth.admin.stop_rpc()
        assert result

    @pytest.mark.asyncio
    async def test_stop_ws(self, async_w3: "AsyncWeb3") -> None:
        result = await async_w3.geth.admin.stop_ws()
        assert result
