from json import JSONDecodeError
import logging
import os
from pathlib import Path
import socket
import sys
import threading
from types import TracebackType
from typing import Any, Optional, Type, Union
from web3._utils.threads import Timeout
from web3.types import RPCEndpoint, RPCResponse
from .base import JSONBaseProvider


class PersistantSocket:
    sock = None

    def __init__(self, ipc_path: str) ->None:
        self.ipc_path = ipc_path

    def __enter__(self) ->socket.socket:
        if not self.ipc_path:
            raise FileNotFoundError(
                f'cannot connect to IPC socket at path: {self.ipc_path!r}')
        if not self.sock:
            self.sock = self._open()
        return self.sock

    def __exit__(self, exc_type: Type[BaseException], exc_value:
        BaseException, traceback: TracebackType) ->None:
        if exc_value is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _open(self) ->socket.socket:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.ipc_path)
        return sock


class IPCProvider(JSONBaseProvider):
    logger = logging.getLogger('web3.providers.IPCProvider')
    _socket = None

    def __init__(self, ipc_path: Union[str, Path]=None, timeout: int=10, *
        args: Any, **kwargs: Any) ->None:
        if ipc_path is None:
            self.ipc_path = get_default_ipc_path()
        elif isinstance(ipc_path, str) or isinstance(ipc_path, Path):
            self.ipc_path = str(Path(ipc_path).expanduser().resolve())
        else:
            raise TypeError('ipc_path must be of type string or pathlib.Path')
        self.timeout = timeout
        self._lock = threading.Lock()
        self._socket = PersistantSocket(self.ipc_path)
        super().__init__()

    def __str__(self) ->str:
        return f'<{self.__class__.__name__} {self.ipc_path}>'

    def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        request = self.encode_rpc_request(method, params)
        with self._lock, self._socket as sock:
            try:
                sock.sendall(request)
                response_raw = b""
                with Timeout(self.timeout) as timeout:
                    while True:
                        try:
                            response_raw += sock.recv(4096)
                        except socket.timeout:
                            timeout.sleep(0)
                            continue
                        if response_raw and response_raw[-1] == ord("\n"):
                            break
            except (ConnectionError, OSError) as e:
                raise ConnectionError(f"Could not connect to IPC socket at path: {self.ipc_path}") from e
        return self.decode_rpc_response(response_raw)

    def isConnected(self) -> bool:
        try:
            with self._lock, self._socket as sock:
                sock.sendall(self.encode_rpc_request("web3_clientVersion", []))
                sock.recv(1)
            return True
        except (ConnectionError, OSError):
            return False

def get_default_ipc_path() -> str:
    if sys.platform.startswith('darwin'):
        return os.path.expanduser("~/Library/Ethereum/geth.ipc")
    elif sys.platform.startswith('linux'):
        return os.path.expanduser("~/.ethereum/geth.ipc")
    elif sys.platform.startswith('win'):
        return r"\\\\.\\pipe\\geth.ipc"
    else:
        raise ValueError(
            "Unsupported platform '{0}'. Unable to determine "
            "the default ipc path.".format(sys.platform)
        )
