from scripts.helpful_scripts import get_account
from brownie import config, network, interface, web3
from scripts.get_weth import get_weth
from web3 import Web3


"""_summary_
Les parametres de la fonction "deposit()" sont les suivants:
    - address asset : qui est l'adresse du token ERC20
    - uint256 amount : qui est le montant du jeton
    - address onBehalfOf : qui l'adresse ou on va deposer le colateral
    - uint16 referralCode : ce parametre est maintenant deprecie, on peut juste mettre un 0 a sa valeur
    """

# 0,05 ether
amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    # Sur le Mainnet fork on appelle la fonction "get_weth"
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    # Pour faire un emprunt on aura besoin d'un ABI et d'une adresse
    lending_pool = get_lending_pool()
    print(lending_pool)
    # Pour deposer nos WETH on devra d'abord approuver ce token ERC20,
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    # Maintenant on peut faire un depot notre token ERC20 sur Aave
    print("Depot en cours")
    transact = lending_pool.deposit(
        erc20_address,
        amount,
        account.address,
        0,
        {"from": account, "gas_price": web3.eth.gas_price},
        # {"from": account, "gas_price": gas_strategy},
    )
    transact.wait(1)
    print("Le depot a ete effectue avec succes...")
    # On cherche le montant que l'on peut emprunter
    borrowable_eth, total_debt = get_borrawable_data(lending_pool, account)
    # Maintenant on va emprunter l'actif DAI
    print("On emprunte...")
    ## DAI en terme d'Ether
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    ## On calcule le montant qu'on peut emprunter en DAI, mais on multiplie le montant total disponible a emprunter par 95% (on peut changer le pourcentage si l'on veut etre plus en securite)
    ## pour nous assurer que notre facteur sante (health factor) est meilleur
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"Nous allons emprunter {amount_dai_to_borrow} DAI")
    amount_dai_wei = Web3.toWei(amount_dai_to_borrow, "ether")
    ## Maintenant on emprunte en appelant la fonction "borrow()" qui prend comme parametre l'addrese du contrat DAI, qu'on peut trouver sur Etherscan
    ## Puis le deuxieme parametre sera le montant a emprunter
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_transact = lending_pool.borrow(
        dai_address,
        amount_dai_wei,
        1,
        0,
        account.address,
        {"from": account, "gas_price": web3.eth.gas_price},
        # {"from": account, "gas_price": gas_strategy},
    )
    borrow_transact.wait(1)
    print(f"On a emprunte un montant de {amount_dai_wei} DAI... Youpiiii!!!")
    ## On appel encore la fonction pour recevoir les donnees d'emprunt
    get_borrawable_data(lending_pool, account)
    # On repaye toutes les dettes empruntees
    # repay_all(amount, lending_pool, account)
    # print(
    #    "On vient juste de deposer, d'emprunter et de repayer avec Aave, Brownie et Chainlink...."
    # )
    # get_borrawable_data(lending_pool, account)


# On cree une fonction pour repayer toutes les dettes
def repay_all(amount, lending_pool, account):
    # On va d'abord appeler la fonction "approve" pour approuver qu'on rembourse
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    # On repaie avec la fonction de Aave "repay"
    repay_transact = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account, "gas_price": web3.eth.gas_price},
        # {"from": account, "gas_price": gas_strategy},
    )
    repay_transact.wait(1)
    print("Montant rembourse...")


# On cree une fonction pour avoir le taux de change entre DAI et ETH
def get_asset_price(price_feed_address):
    # ABI
    # Address
    # Pour avoir l'interface, voir https://github.com/PatrickAlphaC/aave_brownie_py/blob/main/interfaces/AggregatorV3Interface.sol
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    ## On juste recuperer le prix qui se trouve a l'index 1
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"Le prix DAI/ETH est de {converted_latest_price}")
    # return float(latest_price)
    return float(converted_latest_price)


# La fonction pour avoir le montant maximum a emprunter et les donnees de l'utilisateur
def get_borrawable_data(lending_pool, account):
    # On va recuperer toutes les variables dans un tuple
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    # On converti le montant disponible a emprunter, le montant du collateral et de la dette total en Wei
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"Tu as une valeur de : {total_collateral_eth} en ETH depose...")
    print(f"Tu as une valeur de : {total_debt_eth} en ETH de dette...")
    print(
        f"Tu as une valeur de : {available_borrow_eth} en ETH disponible pour emprunter..."
    )
    return (float(available_borrow_eth), float(total_debt_eth))


# La fonction pour approuver le depot de nos token ERC20
def approve_erc20(amount, spender, erc20_address, account):
    # ABI
    # Address
    print("Approbation du jeton ERC20...")
    erc20 = interface.IERC20(erc20_address)
    transact = erc20.approve(
        spender, amount, {"from": account, "gas_price": web3.eth.gas_price}
    )
    transact.wait(1)
    print("Le contrat ERC20 est approuve !!!")
    return transact


# Fonction pour recevoir l'adresse du lending pool
def get_lending_pool():
    # Pour voire le code de l'interface pour l'address provider voir https://docs.aave.com/developers/v/2.0/the-core-protocol/addresses-provider/ilendingpooladdressesprovider
    # et aussi voir https://docs.aave.com/developers/v/2.0/deployed-contracts/deployed-contracts
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    # ABI
    ##Address
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
