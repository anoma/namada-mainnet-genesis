import subprocess
import re
import os
from typing import Dict, List
import toml
import glob
from scripts.constant import VERSION
from utils import is_valid_bech32m

FILE_NAME_PATTERN = r"transactions/(.*)-(validator|bond|account).toml"
EMAIL_PATTERN = r"^\S+@\S+\.\S+$"


def read_env():
    can_apply_for_validators = os.environ.get('CAN_ADD_VALIDATORS', 'true').lower() in ('true', '1', 't')
    can_apply_for_bonds = os.environ.get('CAN_ADD_BONDS', 'true').lower() in ('true', '1', 't')
    can_apply_for_accounts = os.environ.get('CAN_ADD_ACCOUNTS', 'true').lower() in ('true', '1', 't')

    print("Can add validators: {}".format(can_apply_for_validators))
    print("Can add bonds: {}".format(can_apply_for_bonds))
    print("Can add accounts: {}".format(can_apply_for_accounts))

    return can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts


def check_deleted_and_modified_files():
    res = subprocess.run(["git", "diff", "--name-only", "--diff-filter=DM", "origin/main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode > 0:
        exit(1)
    
    files = list(map(lambda file_path: file_path.decode(), res.stdout.splitlines()))
    for file in files:
        print("Found modified/deleted: {}".format(file))

def get_all_created_files(alias):
    res = subprocess.run(["git", "diff", "--name-only", "--diff-filter=AM", "origin/main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode > 0:
        exit(1)

    print("All changes files: {}", res.stdout.splitlines())
    
    return list(filter(lambda file_path: "transactions/{}-".format(alias).lower() in file_path.lower(), map(lambda file_path: file_path.decode().lower(), res.stdout.splitlines())))


def read_unsafe_toml(file_path):
    try:
        with open(file_path, "r") as toml_file:
            return toml.load(toml_file)
    except Exception as e:
        return None
    

def get_alias_from_env():
    alias = os.environ.get("ALIAS")
    if alias is None:
        exit(1)
    return alias.lower()


def get_alias_from_file(file):
    return file.split('/')[1].removesuffix("-validator.toml").removesuffix("-account.toml").removesuffix("-bond.toml")


def check_if_account_is_valid(accounts_toml: List[Dict]):
    for idx, account in enumerate(accounts_toml['established_account']):
        for field in ['vp', 'threshold', 'public_keys']:
            if field not in account:
                print("Invalid reason: account-1-{}".format(idx))
                return False

        vp = account['vp']
        threshold = account['threshold']
        public_keys = account['public_keys']

        if vp != "vp_user":
            print("Invalid reason: account-2-{}".format(idx))
            return False
        
        if len(public_keys) < threshold:
            print("Invalid reason: account-3-{}".format(idx))
            return False

        if threshold <= 0:
            print("Invalid reason: account-4-{}".format(idx))
            return False
        
        for public_key in public_keys:
            is_valid = is_valid_bech32m(public_key, 'tpknam')
            if not is_valid:
                print("Invalid reason: account-5-{}".format(idx))
                return False

    return True

def check_if_validator_is_valid(validators_toml: List[Dict], signatures: List['str']):
    is_valid = check_if_account_is_valid(validators_toml)
    if not is_valid:
        print("Invalid reason: validator-0")
        return False
    
    if 'bond' in validators_toml:
        print("Invalid reason: validator-15-{}".format(idx))
        return False
    
    for idx, validator in enumerate(validators_toml['validator_account']):
        for field in ['consensus_key', 'protocol_key', 'tendermint_node_key', 'eth_hot_key', 'eth_cold_key', 'metadata', 'signatures', 'address', 'vp', 'commission_rate', 'max_commission_rate_change']:
            if field not in validator:
                print("Invalid reason: validator-1-{}".format(idx))
                return False
            
        for field in ['consensus_key', 'protocol_key', 'tendermint_node_key', 'eth_hot_key', 'eth_cold_key']:
            for sub_field in ['pk', 'authorization']:
                if sub_field not in validator[field]:
                    print("Invalid reason: validator-2-{}".format(idx))
                    return False
                
                value = validator[field][sub_field]
                if sub_field == 'pk' and not is_valid_bech32m(value, 'tpknam'):
                    print("Invalid reason: validator-3-{}".format(idx))
                    return False
                elif sub_field == 'authorization' and (not is_valid_bech32m(value, 'signam') or value in signatures):
                    print("Invalid reason: validator-4-{}".format(idx))
                    return False


        for field in ['metadata']:
            for sub_field in ['email']:
                if sub_field not in validator[field]:
                    print("Invalid reason: validator-5-{}".format(idx))
                    return False
                
        if len(validator['signatures']) <= 0:
            print("Invalid reason: validator-6-{}".format(idx))
            return False
        
        for public_key in validator['signatures'].keys():
            if not is_valid_bech32m(public_key, 'tpknam'):
                print("Invalid reason: validator-7-{}".format(idx))
                return False

            sig = validator['signatures'][public_key]
            if not is_valid_bech32m(sig, 'signam'):
                print("Invalid reason: validator-8-{}".format(idx))
                return False
            
            if sig in signatures:
                print("Invalid reason: validator-9-{}".format(idx))
                return False
    
        vp = validator['vp']
        commission_rate = float(validator['commission_rate'])
        max_commission_rate_change = float(validator['max_commission_rate_change'])
        address = validator['address']
        email = validator['metadata']['email']

        if vp != "vp_user":
            print("Invalid reason: validator-14-{}".format(idx))
            return False

        if not 0 <= commission_rate <= 1:
            print("Invalid reason: validator-10-{}".format(idx))
            return False
        
        if not 0 <= max_commission_rate_change <= 1:
            print("Invalid reason: validator-11-{}".format(idx))
            return False
        
        if not re.search(EMAIL_PATTERN, email):
            print("Invalid reason: validator-12-{}".format(idx))
            return False
        
        is_valid = is_valid_bech32m(address, 'tnam')
        if not is_valid:
            print("Invalid reason: validator-13-{}".format(idx))
            return False

    return True


def check_if_bond_is_valid(bonds_toml: List[Dict], signatures: List['str']):
    for idx, bond in enumerate(bonds_toml['bond']):
        for field in ['source', 'validator', 'amount', 'signatures']:
            if field not in bond:
                print("Invalid reason: bond-1-{}".format(idx))
                return False
            
        if len(bond['signatures']) <= 0:
            print("Invalid reason: bond-2-{}".format(idx))
            return False
        
        for public_key in bond['signatures'].keys():
            if not is_valid_bech32m(public_key, 'tpknam'):
                print("Invalid reason: bond-3-{}".format(idx))
                return False

            sig = bond['signatures'][public_key]
            if not is_valid_bech32m(sig, 'signam'):
                print("Invalid reason: bond-4-{}".format(idx))
                return False
            
            if sig in signatures:
                print("Invalid reason: bond-5-{}".format(idx))
                return False
        
        source = bond['source']
        validator = bond['validator']
        
        is_valid = is_valid_bech32m(source, 'tpknam') or is_valid_bech32m(public_key, 'tnam')
        if not is_valid:
            print("Invalid reason: bond-5-{}".format(idx))
            return False
        
        is_valid = is_valid_bech32m(validator, 'tnam')
        if not is_valid:
            print("Invalid reason: bond-6-{}".format(idx))
            return False

    return True


def validate_toml(file, signatures, can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts) -> bool:
    if '-account.toml' in file and can_apply_for_accounts:
        accounts_toml = read_unsafe_toml(file)
        if accounts_toml is None:
            print("{} is NOT valid.".format(file))
            return False
        is_valid = check_if_account_is_valid(accounts_toml)
        if not is_valid:
            print("{} is NOT valid.".format(file))
            return False
    elif '-validator.toml' in file and can_apply_for_validators:
        validators_toml = read_unsafe_toml(file)
        if validators_toml is None:
            print("{} is NOT valid.".format(file))
            return False
        is_valid = check_if_validator_is_valid(validators_toml, signatures)
        if not is_valid:
            print("{} is NOT valid.".format(file))
            return False
    elif '-bond.toml' in file and can_apply_for_bonds:
        bonds_toml = read_unsafe_toml(file)
        if not bonds_toml:
            print("{} is NOT valid.".format(file))
            return False
        is_valid = check_if_bond_is_valid(bonds_toml, signatures)
        if not is_valid:
            print("{} is NOT valid.".format(file))
            return False
    else:
        return False
    
    return True

def read_all_signatures(alias):
    signatures = []
    for file in glob.glob("transactions/*.toml"):
        if alias in file.lower():
            continue
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

    return signatures


def main():
    print("Version: {}".format(VERSION))
    
    alias = get_alias_from_env()
    
    can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts = read_env()
    changed_files = get_all_created_files(alias)

    check_deleted_and_modified_files()

    if len(changed_files) == 0:
        print("No valid found found. Rename to '{}-validator.toml' or '{}-account.toml' or '{}-bond.toml'".format(alias, alias, alias))
        print("Will continue anyway.")
    else:
        print("Found {} file changed/added.".format(len(changed_files)))

    # only files changes in transactions with a specific format are allowed
    for file in changed_files:
        res = re.search(FILE_NAME_PATTERN, file)
        if res is None:
            print("{} doesn't match pattern {}".format(file, FILE_NAME_PATTERN))
            exit(1)

        file_alias = get_alias_from_file(file)
        if not alias.lower() in file_alias.lower():
            print("alias {} doesn't correspond".format(alias.lower()))
            exit(1)

        signatures = read_all_signatures(alias)

        print("{} is allowed, checking if its valid...".format(file))
    
        res = validate_toml(file, signatures, can_apply_for_validators, can_apply_for_bonds, can_apply_for_accounts)
        if res:
            print("{} is valid.".format(file))
        else:
            print("{} is NOT valid".format(file))
            exit(1)


if __name__ == "__main__":
    main()