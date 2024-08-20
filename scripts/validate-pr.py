import subprocess
import re
import os
from typing import Dict, List
import toml
from utils import is_valid_bech32m

FILE_NAME_PATTER = r"transactions/(.*)-(validator|bond|account).toml"
EMAIL_PATTERN = r"^\S+@\S+\.\S+$"


def read_env():
    can_apply_for_validators = os.environ.get('CAN_ADD_VALIDATORS', True).lower() in ('true', '1', 't')
    can_apply_for_bonds = os.environ.get('CAN_ADD_BONDS', True).lower() in ('true', '1', 't')
    can_apply_for_accounts = os.environ.get('CAN_ADD_ACCOUNTS', True).lower() in ('true', '1', 't')

    print("Can add validators: {}", can_apply_for_validators)
    print("Can add bonds: {}", can_apply_for_bonds)
    print("Can add accounts: {}", can_apply_for_accounts)

    return can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts


def check_deleted_and_modified_files(alias):
    res = subprocess.run(["git", "diff", "--name-only", "--diff-filter=DM", "origin/main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode > 0:
        exit(1)
    
    files = list(map(lambda file_path: file_path.decode(), res.stdout.splitlines()))
    for file in files:
        file_alias = get_alias_from_file(file)
        if alias.lower() != file_alias.lower():
            print(alias, file_alias)
            exit(1)

def get_all_created_files():
    res = subprocess.run(["git", "diff", "--name-only", "--diff-filter=AM", "origin/main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode > 0:
        exit(1)
    
    return list(map(lambda file_path: file_path.decode(), res.stdout.splitlines()))


def read_unsafe_toml(file_path):
    try:
        return toml.load(open(file_path, "r"))
    except Exception as e:
        return None
    

def get_alias_from_env():
    alias = os.environ.get("ALIAS")
    if alias is None:
        exit(1)
    return alias


def get_alias_from_file(file):
    return file.split('/')[1].removesuffix("-validator.toml").removesuffix("-account.toml").removesuffix("-bond.toml")


def check_if_account_is_valid(accounts_toml: List[Dict]):
    for account in accounts_toml['established_account']:
        for field in ['vp', 'threshold', 'public_keys']:
            if field not in account:
                return False

        vp = account['vp']
        threshold = account['threshold']
        public_keys = account['public_keys']

        if vp != "vp_user":
            return False
        
        if len(public_keys) < threshold:
            return False

        if threshold <= 0:
            return False
        
        for public_key in public_keys:
            is_valid = is_valid_bech32m(public_key, 'tpknam')
            if not is_valid:
                return False

    return True

def check_if_validator_is_valid(validators_toml: List[Dict]):
    is_valid = check_if_account_is_valid(validators_toml)
    if not is_valid:
        return False
    
    if 'bond' in validators_toml:
        return False
    
    for validator in validators_toml['validator_account']:
        for field in ['consensus_key', 'protocol_key', 'tendermint_node_key', 'eth_hot_key', 'eth_cold_key', 'metadata', 'signatures', 'address', 'vp', 'commission_rate', 'max_commission_rate_change']:
            if field not in validator:
                return False
            
        for field in ['consensus_key', 'protocol_key', 'tendermint_node_key', 'eth_hot_key', 'eth_cold_key']:
            for sub_field in ['pk', 'authorization']:
                if sub_field not in validator[field]:
                    return False
                
                value = validator[field][sub_field]
                if sub_field == 'pk' and not is_valid_bech32m(value, 'tpknam'):
                    return False
                elif sub_field == 'authorization' and not is_valid_bech32m(value, 'signam'):
                    return False

                
        for field in ['metadata']:
            for sub_field in ['email']:
                if sub_field not in validator[field]:
                    return False
                
        if len(validator['signatures']) <= 0:
            return False
        
        for public_key in validator['signatures'].keys():
            if not is_valid_bech32m(public_key, 'tpknam'):
                return False

            sig = validator['signatures'][public_key]
            if not is_valid_bech32m(sig, 'signam'):
                return False
    
        vp = validator['vp']
        commission_rate = float(validator['commission_rate'])
        max_commission_rate_change = float(validator['max_commission_rate_change'])
        address = validator['address']
        email = validator['metadata']['email']

        if vp != "vp_user":
            return False

        if not 0 <= commission_rate <= 1:
            return False
        
        if not 0 <= max_commission_rate_change <= 1:
            return False
        
        if not re.search(EMAIL_PATTERN, email):
            return False
        
        is_valid = is_valid_bech32m(address, 'tnam')
        if not is_valid:
            return False

    return True


def check_if_bond_is_valid(bonds_toml: List[Dict], balances: Dict[str, Dict]):
    for bond in bonds_toml['bond']:
        for field in ['source', 'validator', 'amount', 'signatures']:
            if field not in bond:
                return False
            
        if len(bond['signatures']) <= 0:
            return False
        
        for public_key in bond['signatures'].keys():
            if not is_valid_bech32m(public_key, 'tpknam'):
                return False

            sig = bond['signatures'][public_key]
            if not is_valid_bech32m(sig, 'signam'):
                return False
        
        source = bond['source']
        validator = bond['validator']
        amount = float(bond['amount'])
        
        balance = float(balances[source]) if source in balances else 0

        if balance == 0 or not balance >= amount:
            return False
        
        is_valid = is_valid_bech32m(source, 'tpknam')
        if not is_valid:
            return False
        
        is_valid = is_valid_bech32m(validator, 'tnam')
        if not is_valid:
            return False

    return True


def validate_toml(file, can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts):
    balances = toml.load(open("genesis/balances.toml", "r"))
    nam_balances = balances['token']['NAM']

    if '-account.toml' in file and can_apply_for_accounts:
        accounts_toml = read_unsafe_toml(file)
        if accounts_toml is None:
            print("{} is NOT valid.".format(file))
        is_valid = check_if_account_is_valid(accounts_toml)
        if not is_valid:
            print("{} is NOT valid.".format(file))
    elif '-validator.toml' in file and can_apply_for_validators:
        validators_toml = read_unsafe_toml(file)
        if validators_toml is None:
            print("{} is NOT valid.".format(file))
        is_valid = check_if_validator_is_valid(validators_toml)
        if not is_valid:
            print("{} is NOT valid.".format(file))
    elif '-bond.toml' in file and can_apply_for_bonds:
        bonds_toml = read_unsafe_toml(file)
        if not bonds_toml:
            print("{} is NOT valid.".format(file))
        is_valid = check_if_bond_is_valid(bonds_toml, nam_balances)
        if not is_valid:
            print("{} is NOT valid.".format(file))
    else:
        return False

    print("{} is valid.".format(file))

def main():
    alias = get_alias_from_env()
    check_deleted_and_modified_files(alias)
    
    can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts = read_env()
    changed_files = get_all_created_files()

    print("Found {} file changed/added.".format(len(changed_files)))
    
    # only files changes in transactions with a specific format are allowed
    for file in changed_files:
        res = re.search(FILE_NAME_PATTER, file)
        if res is None:
            print("{} doesn't match pattern {}".format(file, FILE_NAME_PATTER))
            exit(1)

        file_alias = get_alias_from_file(file)
        if not alias.lower() in file_alias.lower():
            exit(1)

        print("{} is allowed, checking if its valid...".format(file))
    
        validate_toml(file, can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts)


if __name__ == "__main__":
    main()