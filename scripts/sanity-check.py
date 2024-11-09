#!/usr/bin/env python3

import subprocess
from decimal import *
import re
import toml


balances_file = 'genesis/balances.toml'
txs_file = 'genesis/transactions.toml'

# Balances sanity check
balances = {}
sum_balances = Decimal('0')
num_addresses = 0

pattern = r"(tnam1q\w+) = \"(\d+\.\d+)\""

# Find all matches in the file content
with open(balances_file, 'r') as file:
    file_content = file.read()

matches = re.findall(pattern, file_content)

# Populate the dictionary with key-value pairs
for match in matches:
    addr, amount = match
    amount = Decimal(amount)
    sum_balances += amount
    num_addresses += 1
    balances[addr] = amount

print('\nNumber of addresses with balance: {}'.format(num_addresses))
print('Total sum of balances: {}'.format(sum_balances))

# Transactions sanity check

bonds = []
sum_bonds = 0
established_accounts = []
validator_accounts = []

def read_unsafe_toml(file_path):
    try:
        return toml.load(open(file_path, "r"))
    except Exception as e:
        return None

txs = read_unsafe_toml(txs_file)

def make_multisig(x):
  return '''#
[[established_account]]
vp = "vp_user"
threshold = {}
public_keys = {}'''.format(x['threshold'], x['public_keys'])

for bond in txs['bond']:
    sum_bonds += Decimal(bond['amount'])

print('Total staked balance: {} ({}% of supply)'.format(sum_bonds, 100 * sum_bonds / sum_balances))

num_multisig = 0
num_singlesig = 0
with_balance = {}

for addr in txs['established_account']:
    if len(addr['public_keys']) > 1:
        num_multisig += 1
    else:
        num_singlesig += 1
    data = make_multisig(addr)
    open('/tmp/transactions.toml', 'w').write(data)
    addr = subprocess.getoutput('namadac utils derive-genesis-addresses --path /tmp/transactions.toml | grep Address | cut -c 28-')
    established_accounts.append(addr)

    if addr in balances:
        with_balance[addr] = balances[addr]
        # print('Established account {} has a balance of {}'.format(addr, balances[addr]))

# print(with_balance)

val_is_subset_of_est = True
for addr in txs['validator_account']:
    validator_accounts.append(addr['address'])
    if addr['address'] not in established_accounts:
        print('WARNING: Validator account {} not found in established accounts'.format(addr['address']))
        val_is_subset_of_est = False


print('\nThere are {} multisig established addresses with > 1 public key'.format(num_multisig))
print('There are {} established addresses that have a balance'.format(len(with_balance)))
print('There are {} established addresses with only 1 public key'.format(num_singlesig))
print('There are {} validator addresses'.format(len(validator_accounts)))
if val_is_subset_of_est:
    print('All validator addresses are found in the derived established addresses')
else:
    print('WARNING: Some validator addresses are not found in the derived established addresses')

print()

# for addr in with_balance:
#     if addr in validator_accounts:
#         print('NOTE: Established account {} with balance was found in init-validator txs'.format(addr))