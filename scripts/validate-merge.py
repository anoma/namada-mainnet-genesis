import glob
import os
import subprocess
import toml

from scripts.constant import VERSION

def get_all_merged_transactions():
    return glob.glob("transactions/*-*.toml")


def read_unsafe_toml(file_path):
    try:
        with open(file_path, "r") as toml_file:
            return toml.load(toml_file)
    except Exception as e:
        return None


def check_duplicate_signature(transactions):
    signatures = []
    for file in transactions:
        if '-validator.toml' in file:
            validators_toml = read_unsafe_toml(file)
            if validators_toml is None:
                print("{} is NOT valid.".format(file))
                continue
            for validator in validators_toml['validator_account']:
                for field in ['consensus_key', 'protocol_key', 'tendermint_node_key', 'eth_hot_key', 'eth_cold_key']:
                    sig = validator[field]['authorization']
                    signatures.append(sig)
                
                for sig in validator['signatures']:
                    signatures.append(sig)
                
        elif '-bond.toml' in file:
            bonds_toml = read_unsafe_toml(file)
            if not bonds_toml:
                print("{} is NOT valid.".format(file))
                continue
            for bond in bonds_toml['bond']:
                for sig in bond['signatures'].values():
                    signatures.append(sig)
        else:
            continue
    
    if len(signatures) != len(set(signatures)):
        print("Duplicate signature detected.")
        exit(1)


def is_valid_template():
    namadac_binaries_path = os.environ.get("NAMADAC_PATH", 'namadac')
    res = subprocess.run([namadac_binaries_path, "utils", "validate-genesis-templates", "--path", "genesis"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode > 0:
        print(res.stderr.decode())
        print("---------")
        print(res.stdout.decode())
        exit(1)
    else:
        print(res.stdout.decode())


def main():
    print("Version: {}".format(VERSION))
    
    transactions = get_all_merged_transactions()
    check_duplicate_signature(transactions)

    genesis_transactions = open("genesis/transactions.toml", "w")

    print("Adding {} transactions...".format(len(transactions)))

    for file in transactions:
        print("Adding {}...".format(file))
        new_transaction = open(file, "r")
        genesis_transactions.write("{}\n".format(new_transaction.read()))

    genesis_transactions.close()

    is_valid_template()

    print("Done.")


if __name__ == "__main__":
    main()
