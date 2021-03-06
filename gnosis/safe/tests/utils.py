import os
from logging import getLogger

from ethereum.transactions import secpk1n
from web3 import Web3

from gnosis.eth.tests.utils import send_tx
from gnosis.eth.utils import get_eth_address_with_key

from ..safe_creation_tx import SafeCreationTx
from ..safe_service import SafeService

logger = getLogger(__name__)


def generate_valid_s():
    while True:
        s = int(os.urandom(30).hex(), 16)
        if s <= (secpk1n // 2):
            return s


def generate_safe(safe_service: SafeService, owners=None, number_owners: int=3, threshold: int=None,
                  gas_price: int=1) -> SafeCreationTx:
    s = generate_valid_s()

    if not owners:
        owners = []
        for _ in range(number_owners):
            owner, _ = get_eth_address_with_key()
            owners.append(owner)

    threshold = threshold if threshold else len(owners)

    return safe_service.build_safe_creation_tx(s, owners, threshold, gas_price=gas_price, payment_token=None)


def deploy_safe(w3: Web3, safe_creation_tx: SafeCreationTx, funder: str, initial_funding_wei: int = 0,
                funder_account=None) -> str:
    if funder_account:
        send_tx(w3, {
            'to': safe_creation_tx.deployer_address,
            'value': safe_creation_tx.payment,
        }, funder_account)

        send_tx(w3, {
            'to': safe_creation_tx.safe_address,
            'value': safe_creation_tx.payment + initial_funding_wei,
        }, funder_account)
    else:
        w3.eth.waitForTransactionReceipt(
            w3.eth.sendTransaction({
                'from': funder,
                'to': safe_creation_tx.deployer_address,
                'value': safe_creation_tx.payment
            })
        )

        w3.eth.waitForTransactionReceipt(
            w3.eth.sendTransaction({
                'from': funder,
                'to': safe_creation_tx.safe_address,
                'value': safe_creation_tx.payment + initial_funding_wei
            })
        )

    tx_hash = w3.eth.sendRawTransaction(bytes(safe_creation_tx.tx_raw))
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    assert tx_receipt.contractAddress == safe_creation_tx.safe_address
    assert tx_receipt.status

    return safe_creation_tx.safe_address
