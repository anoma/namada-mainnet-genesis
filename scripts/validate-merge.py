import glob
import os
import subprocess

def get_all_merged_transactions():
    return glob.glob("transactions/*-*.toml")


def is_valid_template():
    namadac_binaries_path = os.environ.get("NAMADAC_PATH", 'namadac')
    res = subprocess.run([namadac_binaries_path, "utils", "validate-genesis-templates", "--path", "genesis"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode > 0:
        print(res.stderr)
        print("---------")
        print(res.stdout)
        exit(1)


def main():
    transactions = get_all_merged_transactions()
    genesis_transactions = open("genesis/transactions.toml", "w")

    print("Adding {} transactions...".format(len(transactions)))

    for file in transactions:
        print("Adding {}...".format(file))
        new_transaction = open(file, "r")
        genesis_transactions.write("{}\n".format(new_transaction.read()))

    # flush write buffer
    genesis_transactions.close()

    is_valid_template()

    print("Done.")


if __name__ == "__main__":
    main()
