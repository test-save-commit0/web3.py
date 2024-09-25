import asyncio
import pytest
from typing import TYPE_CHECKING, Any, Dict, Tuple, cast
from eth_utils import is_hexstr
from hexbytes import HexBytes
from web3.datastructures import AttributeDict
from web3.middleware import async_geth_poa_middleware
from web3.types import FormattedEthSubscriptionResponse
if TYPE_CHECKING:
    from web3.main import _PersistentConnectionWeb3


class PersistentConnectionProviderTest:
    @pytest.mark.asyncio
    async def test_persistent_connection_provider(self, async_w3: "_PersistentConnectionWeb3") -> None:
        async_w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
        
        async with async_w3.persistent_websocket() as ws:
            subscription_id = await ws.eth.subscribe("newHeads")
            assert is_hexstr(subscription_id)

            # Wait for the next block
            response = await ws.receive()
            formatted_response = self._format_subscription_response(response)

            assert formatted_response["subscription"] == subscription_id
            assert "result" in formatted_response
            assert isinstance(formatted_response["result"], AttributeDict)
            assert "number" in formatted_response["result"]

            # Unsubscribe
            success = await ws.eth.unsubscribe(subscription_id)
            assert success is True

    def _format_subscription_response(
        self, response: Dict[str, Any]
    ) -> FormattedEthSubscriptionResponse:
        return cast(
            FormattedEthSubscriptionResponse,
            {
                "subscription": HexBytes(response["params"]["subscription"]).hex(),
                "result": AttributeDict(response["params"]["result"]),
            },
        )

    @pytest.mark.asyncio
    async def test_persistent_connection_provider_with_middleware(
        self, async_w3: "_PersistentConnectionWeb3"
    ) -> None:
        async def middleware(make_request, w3):
            async def middleware_fn(method, params):
                if method == "eth_blockNumber":
                    return {"result": "0x1234"}
                return await make_request(method, params)
            return middleware_fn

        async_w3.middleware_onion.add(middleware)

        async with async_w3.persistent_websocket() as ws:
            block_number = await ws.eth.block_number
            assert block_number == 0x1234

    @pytest.mark.asyncio
    async def test_persistent_connection_provider_multiple_requests(
        self, async_w3: "_PersistentConnectionWeb3"
    ) -> None:
        async with async_w3.persistent_websocket() as ws:
            tasks = [
                ws.eth.chain_id,
                ws.eth.block_number,
                ws.eth.gas_price,
            ]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(isinstance(result, int) for result in results)

    @pytest.mark.asyncio
    async def test_persistent_connection_provider_error_handling(
        self, async_w3: "_PersistentConnectionWeb3"
    ) -> None:
        async with async_w3.persistent_websocket() as ws:
            with pytest.raises(ValueError):
                await ws.eth.get_block("invalid_block_identifier")
