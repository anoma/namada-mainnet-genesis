# Building Mainnet genesis archive

- Run `./scripts/make-mainnet-genesis.sh`
- It will output the genesis files in an archive called `namada.a26cb3db6ea69843b6e86ce.tar.gz`.

# Pregenesis flow validation scripts

A set of scripts used by CI to validate the pre-genesis file submissions.

## Pre-requisted
Its highly recommended to run all the python scripts below locally before opening a PR. In order to do so, some steps are required:
- [install poetry](https://python-poetry.org/docs/)
- run `poetry install`
- [install namada](https://docs.namada.net/introduction/install) binaries

## Light validation on PR

Each PR is validated by `validate-pr.py` which checks if the submission makes generally sense. Each submitted file should be placed in the `transactions` folder and must have the following format:
- `transactions/<github_handle>-(validator|account|bond).toml`
    - example: `transactions/fraccaman-validator.toml`
    - example: `transactions/fraccaman-bond.toml`

Pre-genesis validator submission MUST not contain a self bond. If you want to bond to your validator, submit a `bond` pre-genesis transaction from your tpknam.

You can and should run this locally before opening a PR:
- `ALIAS=<github_handle> poetry run python3 scripts/validate-pr.py`

## Deep validation on PR merges

Once a PR is reviewed passes the CI checks (i.e is green) and is reviewed by at least 1 person, it's sent to the merge queue. Here, CI run a second validation, which basically tries to merge the transaction/s into the genesis file and check if the resulting genesis file is valid. If the check fail, the PR is remvoed from the merge queue and the author will have to fix w/e is broken.
If the check is successful, the transactions are added to the genenesis file. No more actions are required by the PR author.

You can and should run this locally before opening a PR:
- `NAMADA_PATH=<path_to_namada_binaries> poetry run python3 scripts/merge-pr.py`


## PR lands on `main`
Every PR passing the aforementioned checks will be merged into the genesis file (specifically into `transactions.toml`). CI will also create a [README](genesis/README.md) with a list of validators and a graph rapressing voting power distribution.
