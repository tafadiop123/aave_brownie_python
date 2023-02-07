from scripts.helpful_scripts import get_account
from brownie import interface, config, network, accounts
from brownie import web3


def main():
    get_weth()


def get_weth():
    """
    - En déposant des ETH dans le contrat WETH, on recevra un jeton WETH.
    - Pour ce faire on aura besoin d'un ABI et d'une addresse du contrat WETH.
    - On peut utiliser l'interface "WethInterface.sol" https://github.com/PatrickAlphaC/aave_brownie_py/tree/main/interfaces
    """
    account = get_account()
    # account = accounts[0]
    # On instance l'interface qui permet de changer les ETH en WETH
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    ##On va faire un depot de 0,05 Ether
    transact = weth.deposit(
        {"from": account, "value": 0.1 * 10**18, "gas_price": web3.eth.gas_price}
    )
    ##On va attendre que la transaction precedente se termine
    transact.wait(1)
    print("Un montant de 0,1 ETH a ete converti en WETH !")
    return transact
