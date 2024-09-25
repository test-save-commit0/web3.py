import pytest
from typing import Any, NoReturn, Sequence, Union
from eth_typing import ChecksumAddress, HexAddress, HexStr, TypeStr
from hexbytes import HexBytes
from web3 import AsyncWeb3, Web3
from web3._utils.ens import ens_addresses
from web3.exceptions import InvalidAddress


class Web3ModuleTest:
    def test_web3_clientVersion(self, web3: Union[Web3, AsyncWeb3]) -> None:
        client_version = web3.clientVersion
        assert isinstance(client_version, str)
        assert len(client_version) > 0

    def test_web3_api_deprecated(self, web3: Union[Web3, AsyncWeb3]) -> None:
        with pytest.warns(DeprecationWarning):
            assert web3.api == "web3"

    def test_web3_sha3(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.sha3(0x678901) == HexBytes('0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45')
        assert web3.sha3(text='web3.py') == HexBytes('0x64e604787cbf194841e7b68d7cd28786f6c9a0a3ab9f8b0a0e87cb4387ab0107')
        assert web3.sha3(hexstr='0x80') == HexBytes('0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421')
        assert web3.sha3(b'\x01\x02\x03') == HexBytes('0x6e519b1ba5fabfa25f89f1dbe6037ec016d3dc33c0a6e4f56a5f33a93b99db80')

    def test_web3_to_hex(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.to_hex(b'\x01\x02\x03') == '0x010203'
        assert web3.to_hex('abc') == '0x616263'
        assert web3.to_hex(12345) == '0x3039'

    def test_web3_to_text(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.to_text(HexBytes('0x666f6f626172')) == 'foobar'
        assert web3.to_text('0x666f6f626172') == 'foobar'
        assert web3.to_text(b'foobar') == 'foobar'

    def test_web3_to_bytes(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.to_bytes(HexBytes('0x666f6f626172')) == b'foobar'
        assert web3.to_bytes('0x666f6f626172') == b'foobar'
        assert web3.to_bytes(b'foobar') == b'foobar'

    def test_web3_is_address(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.is_address('0xd3CdA913deB6f67967B99D67aCDFa1712C293601')
        assert not web3.is_address('0xd3CdA913deB6f67967B99D67aCDFa1712C293601#')
        assert not web3.is_address('0xd3CdA913deB6f67967B99D67aCDFa1712C293601#')
        assert not web3.is_address('0xd3CdA913deB6f67967B99D67aCDFa1712C293601@')

    def test_web3_is_checksum_address(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.is_checksum_address('0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed')
        assert not web3.is_checksum_address('0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed')
        assert not web3.is_checksum_address('0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed#')

    def test_web3_to_checksum_address(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.to_checksum_address('0xd3cda913deb6f67967b99d67acdfa1712c293601') == '0xd3CdA913deB6f67967B99D67aCDFa1712C293601'
        with pytest.raises(InvalidAddress):
            web3.to_checksum_address('0xd3cda913deb6f67967b99d67acdfa1712c293601#')

    def test_web3_is_connected(self, web3: Union[Web3, AsyncWeb3]) -> None:
        assert web3.is_connected()
