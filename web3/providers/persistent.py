from abc import ABC
import asyncio
import logging
from typing import Optional
from websockets import ConnectionClosed, ConnectionClosedOK, WebSocketClientProtocol, WebSocketException
from web3._utils.caching import generate_cache_key
from web3.exceptions import ProviderConnectionError, TaskNotRunning, TimeExhausted
from web3.providers.async_base import AsyncJSONBaseProvider
from web3.providers.websocket.request_processor import RequestProcessor
from web3.types import RPCId, RPCResponse
DEFAULT_PERSISTENT_CONNECTION_TIMEOUT = 50.0


class PersistentConnectionProvider(AsyncJSONBaseProvider, ABC):
    logger = logging.getLogger('web3.providers.PersistentConnectionProvider')
    has_persistent_connection = True
    endpoint_uri: Optional[str] = None
    _max_connection_retries: int = 5
    _ws: Optional[WebSocketClientProtocol] = None
    _request_processor: RequestProcessor
    _message_listener_task: Optional['asyncio.Task[None]'] = None
    _listen_event: asyncio.Event = asyncio.Event()

    def __init__(self, request_timeout: float=
        DEFAULT_PERSISTENT_CONNECTION_TIMEOUT,
        subscription_response_queue_size: int=500,
        request_information_cache_size: int=500,
        silence_listener_task_exceptions: bool=False) ->None:
        super().__init__()
        self._request_processor = RequestProcessor(self,
            subscription_response_queue_size=
            subscription_response_queue_size,
            request_information_cache_size=request_information_cache_size)
        self.request_timeout = request_timeout
        self.silence_listener_task_exceptions = (
            silence_listener_task_exceptions)

    def _error_log_listener_task_exception(self, e: Exception) ->None:
        """
        When silencing listener task exceptions, this method is used to log the
        exception and keep the listener task alive. Override this method to fine-tune
        error logging behavior for the implementation class.
        """
        self.logger.error(f"Listener task exception: {e}", exc_info=True)

    def _handle_listener_task_exceptions(self) ->None:
        """
        Should be called every time a `PersistentConnectionProvider` is polling for
        messages in the main loop. If the message listener task has completed and an
        exception was recorded, raise the exception in the main loop.
        """
        if self._message_listener_task and self._message_listener_task.done():
            exception = self._message_listener_task.exception()
            if exception:
                if self.silence_listener_task_exceptions:
                    self._error_log_listener_task_exception(exception)
                    # Restart the listener task
                    self._start_listener_task()
                else:
                    raise exception

    def _start_listener_task(self) ->None:
        """
        Start the message listener task.
        """
        if self._message_listener_task is None or self._message_listener_task.done():
            self._message_listener_task = asyncio.create_task(self._listen_for_messages())

    async def _listen_for_messages(self) ->None:
        """
        Listen for messages from the WebSocket connection.
        """
        while True:
            try:
                if self._ws:
                    message = await self._ws.recv()
                    await self._request_processor.process_response(message)
            except (ConnectionClosed, ConnectionClosedOK, WebSocketException) as e:
                self.logger.warning(f"WebSocket connection closed: {e}")
                await self._reconnect()
            except Exception as e:
                self.logger.error(f"Error in message listener: {e}", exc_info=True)
                if not self.silence_listener_task_exceptions:
                    raise

    async def _reconnect(self) ->None:
        """
        Attempt to reconnect to the WebSocket.
        """
        for attempt in range(self._max_connection_retries):
            try:
                await self.connect()
                self.logger.info("Reconnected to WebSocket")
                return
            except Exception as e:
                self.logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        raise ProviderConnectionError("Failed to reconnect after multiple attempts")

    async def connect(self) ->None:
        """
        Establish a WebSocket connection.
        """
        if not self.endpoint_uri:
            raise ValueError("No endpoint URI specified")
        
        try:
            self._ws = await asyncio.wait_for(
                WebSocketClientProtocol.__aenter__(self.endpoint_uri),
                timeout=self.request_timeout
            )
            self._start_listener_task()
            self._listen_event.set()
        except (asyncio.TimeoutError, WebSocketException) as e:
            raise ProviderConnectionError(f"Failed to connect to {self.endpoint_uri}: {e}")

    async def disconnect(self) ->None:
        """
        Close the WebSocket connection.
        """
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._message_listener_task:
            self._message_listener_task.cancel()
            try:
                await self._message_listener_task
            except asyncio.CancelledError:
                pass
        self._listen_event.clear()

    async def is_connected(self) ->bool:
        """
        Check if the WebSocket connection is established and open.
        """
        return self._ws is not None and self._ws.open

    async def make_request(self, method: RPCEndpoint, params: Any) ->RPCResponse:
        """
        Make an RPC request over the WebSocket connection.
        """
        if not await self.is_connected():
            await self.connect()

        request_id = generate_cache_key(method, params)
        request = self.encode_rpc_request(method, params)

        try:
            response = await asyncio.wait_for(
                self._request_processor.send_request(request_id, request),
                timeout=self.request_timeout
            )
            return self.decode_rpc_response(response)
        except asyncio.TimeoutError:
            raise TimeExhausted(f"Request {request_id} timed out after {self.request_timeout} seconds")
        except Exception as e:
            raise ProviderConnectionError(f"Error making request: {e}")
