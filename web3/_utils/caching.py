import collections
import hashlib
from typing import TYPE_CHECKING, Any, Callable, List, Tuple
from eth_utils import is_boolean, is_bytes, is_dict, is_list_like, is_null, is_number, is_text, to_bytes
if TYPE_CHECKING:
    from web3.types import RPCEndpoint


def generate_cache_key(value: Any) -> str:
    """
    Generates a cache key for the *args and **kwargs
    """
    if is_null(value):
        return "null"
    elif is_boolean(value):
        return "bool:%s" % str(value).lower()
    elif is_number(value):
        return "num:%d" % value
    elif is_text(value):
        return "text:%s" % value
    elif is_bytes(value):
        return "bytes:%s" % hashlib.md5(value).hexdigest()
    elif is_list_like(value):
        return "list:%s" % hashlib.md5(to_bytes(str(value))).hexdigest()
    elif is_dict(value):
        return "dict:%s" % hashlib.md5(to_bytes(str(sorted(value.items())))).hexdigest()
    else:
        return "obj:%s" % hashlib.md5(to_bytes(str(value))).hexdigest()


class RequestInformation:

    def __init__(self, method: 'RPCEndpoint', params: Any,
        response_formatters: Tuple[Callable[..., Any], ...],
        subscription_id: str=None):
        self.method = method
        self.params = params
        self.response_formatters = response_formatters
        self.subscription_id = subscription_id
        self.middleware_response_processors: List[Callable[..., Any]] = []
