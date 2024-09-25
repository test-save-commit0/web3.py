from eth_typing import ChecksumAddress, HexAddress
from eth_utils import keccak, to_bytes, to_checksum_address
import rlp
from web3.types import HexStr, Nonce


def get_create_address(sender: HexAddress, nonce: Nonce) ->ChecksumAddress:
    """
    Determine the resulting `CREATE` opcode contract address for a sender and a nonce.
    """
    sender_bytes = to_bytes(hexstr=sender)
    nonce_bytes = rlp.encode(nonce)
    raw_address = keccak(rlp.encode([sender_bytes, nonce_bytes]))
    return to_checksum_address(raw_address[12:])


def get_create2_address(sender: HexAddress, salt: HexStr, init_code: HexStr
    ) ->ChecksumAddress:
    """
    Determine the resulting `CREATE2` opcode contract address for a sender, salt and
    bytecode.
    """
    prefix = b'\xff'
    sender_bytes = to_bytes(hexstr=sender)
    salt_bytes = to_bytes(hexstr=salt)
    init_code_bytes = to_bytes(hexstr=init_code)
    init_code_hash = keccak(init_code_bytes)
    raw_address = keccak(prefix + sender_bytes + salt_bytes + init_code_hash)
    return to_checksum_address(raw_address[12:])
