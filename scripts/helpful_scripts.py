from brownie import accounts, network, config

# On definit nos environnements de developpement
LOCAL_BLOCKCHAIN_ENVIRONMENTS = [
    "development",
    "ganache-local",
    "hardhat",
    "ganache",
    "mainnet-fork",
]

def get_account(index=None, id=None):
    # if network.show_active() == "development":
    if index:
        return accounts[index]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print(accounts[0].balance())
        return accounts[0]
    if id:
        return accounts.load(id)
    if network.show_active() in config["networks"]:
        return accounts.add(config["wallets"]["from_key"])
    return None