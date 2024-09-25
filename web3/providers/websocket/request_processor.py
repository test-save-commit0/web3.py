import asyncio
from copy import copy
import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, Optional, Tuple, TypeVar, Union
from web3._utils.caching import RequestInformation, generate_cache_key
from web3.exceptions import TaskNotRunning
from web3.types import RPCEndpoint, RPCResponse
from web3.utils import SimpleCache
if TYPE_CHECKING:
    from web3.providers.persistent import PersistentConnectionProvider
T = TypeVar('T')
if sys.version_info >= (3, 9):


    class _TaskReliantQueue(asyncio.Queue[T], Generic[T]):
        pass
else:


    class _TaskReliantQueue(asyncio.Queue, Generic[T]):
        pass


class TaskReliantQueue(_TaskReliantQueue[T]):
    """
    A queue that relies on a task to be running to process items in the queue.
    """


class RequestProcessor:
    _subscription_queue_synced_with_ws_stream: bool = False

    def __init__(self, provider: 'PersistentConnectionProvider',
        subscription_response_queue_size: int=500,
        request_information_cache_size: int=500) ->None:
        self._provider = provider
        self._request_response_cache: SimpleCache = SimpleCache(500)
        self._subscription_response_queue: TaskReliantQueue[Union[
            RPCResponse, TaskNotRunning]] = TaskReliantQueue(maxsize=
            subscription_response_queue_size)
        self._request_information_cache: SimpleCache = SimpleCache(
            request_information_cache_size)

    def _bump_cache_if_key_present(self, cache_key: str, request_id: int
        ) ->None:
        """
        If the cache key is present in the cache, bump the cache key and request id
        by one to make room for the new request. This behavior is necessary when a
        request is made but inner requests, say to `eth_estimateGas` if the `gas` is
        missing, are made before the original request is sent.
        """
        if cache_key in self._request_information_cache:
            old_request_info = self._request_information_cache[cache_key]
            new_request_id = old_request_info.request_id + 1
            new_cache_key = generate_cache_key(
                old_request_info.method,
                old_request_info.params,
                new_request_id
            )
            self._request_information_cache[new_cache_key] = RequestInformation(
                old_request_info.method,
                old_request_info.params,
                new_request_id
            )
            del self._request_information_cache[cache_key]

    def clear_caches(self) ->None:
        """
        Clear the request processor caches.
        """
        self._request_response_cache.clear()
        self._request_information_cache.clear()
