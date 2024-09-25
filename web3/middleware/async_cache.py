from concurrent.futures import ThreadPoolExecutor
import threading
from typing import TYPE_CHECKING, Any, Callable, Collection
from web3._utils.async_caching import async_lock
from web3._utils.caching import generate_cache_key
from web3.middleware.cache import SIMPLE_CACHE_RPC_WHITELIST, _should_cache_response
from web3.types import AsyncMiddleware, AsyncMiddlewareCoroutine, Middleware, RPCEndpoint, RPCResponse
from web3.utils.caching import SimpleCache
if TYPE_CHECKING:
    from web3 import AsyncWeb3, Web3
_async_request_thread_pool = ThreadPoolExecutor()


async def async_construct_simple_cache_middleware(cache: SimpleCache=None,
    rpc_whitelist: Collection[RPCEndpoint]=SIMPLE_CACHE_RPC_WHITELIST,
    should_cache_fn: Callable[[RPCEndpoint, Any, RPCResponse], bool]=
    _should_cache_response) ->AsyncMiddleware:
    """
    Constructs a middleware which caches responses based on the request
    ``method`` and ``params``

    :param cache: A ``SimpleCache`` class.
    :param rpc_whitelist: A set of RPC methods which may have their responses cached.
    :param should_cache_fn: A callable which accepts ``method`` ``params`` and
        ``response`` and returns a boolean as to whether the response should be
        cached.
    """
    if cache is None:
        cache = SimpleCache(256)

    async def async_middleware(make_request: Callable[[RPCEndpoint, Any], Any], w3: "AsyncWeb3") -> AsyncMiddlewareCoroutine:
        async def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
            if method in rpc_whitelist:
                cache_key = generate_cache_key((method, params))
                cached_response = cache.get(cache_key)
                if cached_response is not None:
                    return cached_response

                response = await make_request(method, params)

                if should_cache_fn(method, params, response):
                    async with async_lock():
                        cache.cache(cache_key, response)

                return response
            else:
                return await make_request(method, params)

        return middleware

    return async_middleware
