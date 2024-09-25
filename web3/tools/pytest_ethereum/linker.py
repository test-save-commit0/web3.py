import logging
from typing import Any, Callable, Dict
from eth_typing import ContractName
from eth_utils import to_checksum_address, to_hex
from eth_utils.toolz import assoc_in, curry, pipe
from ethpm import Package
from ethpm.uri import create_latest_block_uri
from web3.tools.pytest_ethereum._utils import create_deployment_data, get_deployment_address, insert_deployment
from web3.tools.pytest_ethereum.exceptions import LinkerError
logger = logging.getLogger('pytest_ethereum.linker')


def deploy(contract_name: str, *args: Any, transaction: Dict[str, Any]=None
    ) ->Callable[..., Package]:
    """
    Return a newly created package and contract address.
    Will deploy the given contract_name, if data exists in package. If
    a deployment is found on the current w3 instance, it will return that deployment
    rather than creating a new instance.
    """
    def _deploy(package: Package) -> Package:
        deployments = package.deployments
        if contract_name in deployments:
            return package

        factory = package.get_contract_factory(contract_name)
        if not factory:
            raise LinkerError(f"Contract factory for {contract_name} not found in package.")

        w3 = package.w3
        if transaction is None:
            deploy_transaction = {}
        else:
            deploy_transaction = transaction.copy()
        
        if "from" not in deploy_transaction:
            deploy_transaction["from"] = w3.eth.accounts[0]

        tx_hash = factory.constructor(*args).transact(deploy_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        address = tx_receipt["contractAddress"]

        deployment_data = create_deployment_data(
            contract_name,
            to_checksum_address(address),
            tx_receipt,
        )
        latest_block_uri = create_latest_block_uri(w3, tx_receipt)
        return insert_deployment(
            package,
            contract_name,
            deployment_data,
            latest_block_uri
        )

    return _deploy


@curry
def link(contract: ContractName, linked_type: str, package: Package) ->Package:
    """
    Return a new package, created with a new manifest after applying the linked type
    reference to the contract factory.
    """
    deployment_address = get_deployment_address(package, linked_type)
    if not deployment_address:
        raise LinkerError(f"No deployment found for contract {linked_type}")

    factory = package.get_contract_factory(contract)
    if not factory:
        raise LinkerError(f"Contract factory for {contract} not found in package.")

    linked_factory = factory.link_bytecode({linked_type: deployment_address})

    # Update the contract factory in the package
    updated_manifest = pipe(
        package.manifest,
        lambda manifest: assoc_in(
            manifest,
            ["contract_types", contract, "deployment_bytecode", "bytecode"],
            to_hex(linked_factory.bytecode)
        )
    )

    return Package(updated_manifest, package.w3)


@curry
def run_python(callback_fn: Callable[..., None], package: Package) ->Package:
    """
    Return the unmodified package, after performing any user-defined
    callback function on the contracts in the package.
    """
    callback_fn(package)
    return package
