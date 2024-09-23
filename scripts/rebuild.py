from collections import defaultdict
import glob
import toml
import os
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader

TOTAL_SUPPLY = 1000000000

def build_graph(validators):
    validators_with_non_zero_stake = list(filter(lambda x: x['voting_power'] > 0, validators))
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[validator['alias'] if validator['alias'] else validator['address'] for validator in validators_with_non_zero_stake[:150]],
        y=[validator['voting_power'] for validator in validators_with_non_zero_stake[:150]],
        name='validators',
        marker_color='indianred'
    ))

    fig.update_layout(
        xaxis={'categoryorder':'total descending'},
        autosize=False,
        width=1500,
        height=750,
        title="First 150 validators, sorted by voting power, with stake > 0"
    )
    fig.update_xaxes(
        tickangle=75,
    )
    fig.update_yaxes(automargin=True)

    fig.write_image("images/validators.png")


def build_readme(validators):
    environment = Environment(loader=FileSystemLoader("scripts/artifacts"))
    template = environment.get_template("README.jinja")

    total_staked_tokens = sum(map(lambda x: x['voting_power'], validators))
    total_staked_token_percentage = round((total_staked_tokens / TOTAL_SUPPLY) * 100, 2)
    total_delegations = sum(map(lambda x: x['total_delegations'], validators))

    print(total_delegations)

    content = template.render({
        "validators": validators, 
        "total_staked_token_percentage": total_staked_token_percentage, 
        "total_staked_tokens": total_staked_tokens,
        "total_delegations": total_delegations
    })

    with open("README.md", mode="w", encoding="utf-8") as message:
        message.write(content)


def read_unsafe_toml(file_path):
    try:
        return toml.load(open(file_path, "r"))
    except Exception as e:
        return None


def get_alias():
    alias = os.environ.get("ALIAS")
    if alias is None:
        exit(1)
    return alias


def parse_validators():
    validator_files = glob.glob("transactions/*-validator.toml")
    bond_files = glob.glob("transactions/*-bond.toml")

    bonds = []
    target_vp = defaultdict(int)
    target_delegations = defaultdict(int)
    for file in bond_files:
        bonds_toml = read_unsafe_toml(file)
        if bonds_toml is None:
            continue
        
        for bond in bonds_toml['bond']:
            bonds.append({
                'source': bond['source'],
                'validator': bond['validator'],
                'amount': bond['amount'],
            })
            target_vp[bond['validator']] += float(bond['amount'])
            target_delegations[bond['validator']] += 1

    validators = []
    for file in validator_files:
        validators_toml = read_unsafe_toml(file)
        if validators_toml is None:
            continue

        for validator in validators_toml['validator_account']:
            validators.append({
                'address': validator['address'],
                'commission_rate': float(validator['commission_rate']) * 100,
                'max_commission_rate_change': float(validator['max_commission_rate_change']) * 100,
                'email': validator['metadata']['email'],
                'alias': validator['metadata']['name'] if 'name' in validator['metadata'] else None,
                'website': validator['metadata']['website'] if 'website' in validator['metadata'] else None,
                'voting_power': target_vp[validator['address']] if validator['address'] in target_vp else 0,
                'total_delegations': target_delegations[validator['address']] if validator['address'] in target_delegations else 0,
            })

    return sorted(validators, key=lambda d: d['voting_power'], reverse=True)


def merge_transactions():
    transactions = glob.glob("transactions/*-*.toml")
    genesis_transactions = open("genesis/transactions.toml", "w")

    print("Adding {} transactions...".format(len(transactions)))

    for index, file in enumerate(transactions):
        print("Adding {}...".format(file))
        alias = file.split("/")[1].split(".")[0].lower()
        if index == 0:
            genesis_transactions.write("# adding transaction for {}\n\n".format(alias))
        else:
            genesis_transactions.write("\n\n# adding transaction for {}\n\n".format(alias))
        new_transaction = open(file, "r")
        genesis_transactions.write("{}\n".format(new_transaction.read()))

    print("Done.")


def main():
    validators = parse_validators()
    build_graph(validators)
    build_readme(validators)
    merge_transactions()

if __name__ == "__main__":
    main()