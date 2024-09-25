from typing import Optional, Any, Dict, List
from web3._utils.rpc_abi import RPC
from web3.module import Module
from web3.types import Wei, BlockIdentifier


class Testing(Module):
    def timeTravel(self, timestamp: int) -> bool:
        """
        Fast forward to a future timestamp.

        :param timestamp: The timestamp to fast forward to.
        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(RPC.testing_timeTravel, [timestamp])

    def mine(self, num_blocks: int = 1) -> bool:
        """
        Mine a specified number of blocks.

        :param num_blocks: Number of blocks to mine (default: 1).
        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(RPC.evm_mine, [num_blocks])

    def snapshot(self) -> str:
        """
        Take a snapshot of the current state of the blockchain.

        :return: The ID of the snapshot.
        """
        return self.web3.manager.request_blocking(RPC.evm_snapshot, [])

    def revert(self, snapshot_id: str) -> bool:
        """
        Revert the blockchain to a previous snapshot.

        :param snapshot_id: The ID of the snapshot to revert to.
        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(RPC.evm_revert, [snapshot_id])

    def reset_to_genesis(self) -> bool:
        """
        Reset the blockchain to its genesis state.

        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(RPC.evm_reset, [])

    def set_balance(self, address: str, balance: Wei) -> bool:
        """
        Set the balance of an account.

        :param address: The address of the account.
        :param balance: The new balance in Wei.
        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(
            RPC.testing_setBalance,
            [address, hex(balance)]
        )

    def set_code(self, address: str, code: str) -> bool:
        """
        Set the code of a contract.

        :param address: The address of the contract.
        :param code: The new code as a hexadecimal string.
        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(
            RPC.testing_setCode,
            [address, code]
        )

    def set_storage_at(self, address: str, position: int, value: str) -> bool:
        """
        Set a storage slot of a contract.

        :param address: The address of the contract.
        :param position: The storage slot position.
        :param value: The value to set at the storage slot.
        :return: True if successful, False otherwise.
        """
        return self.web3.manager.request_blocking(
            RPC.testing_setStorageAt,
            [address, hex(position), value]
        )

    def get_block_by_number(self, block_identifier: BlockIdentifier) -> Dict[str, Any]:
        """
        Get block information by block number.

        :param block_identifier: The block number or a predefined block identifier.
        :return: A dictionary containing block information.
        """
        return self.web3.manager.request_blocking(
            RPC.eth_getBlockByNumber,
            [block_identifier, True]
        )

    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get the receipt of a transaction.

        :param tx_hash: The transaction hash.
        :return: A dictionary containing the transaction receipt.
        """
        return self.web3.manager.request_blocking(
            RPC.eth_getTransactionReceipt,
            [tx_hash]
        )

    def get_logs(self, from_block: BlockIdentifier, to_block: BlockIdentifier, address: Optional[str] = None, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get logs matching the given parameters.

        :param from_block: The starting block (inclusive).
        :param to_block: The ending block (inclusive).
        :param address: (Optional) The address to get logs from.
        :param topics: (Optional) Array of 32 Bytes DATA topics.
        :return: A list of log objects.
        """
        filter_params = {
            "fromBlock": from_block,
            "toBlock": to_block,
        }
        if address:
            filter_params["address"] = address
        if topics:
            filter_params["topics"] = topics

        return self.web3.manager.request_blocking(
            RPC.eth_getLogs,
            [filter_params]
        )
