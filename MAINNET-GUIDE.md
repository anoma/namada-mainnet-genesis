# Namada Mainnet - guide for validators, full nodes, and users

### Summary:
- Namada binaries version: **[v1.0.0](https://github.com/anoma/namada/releases/tag/v1.0.0)**
- CometBFT version **[v0.37.11](https://github.com/cometbft/cometbft/releases/tag/v0.37.11)**
- Chain-id: **namada.5f5de2dd1b88cba30586420**
- Starts: **Tuesday, December 3 @ 15:00 UTC**

### Instructions for genesis validators:

1. Install Namada **[v1.0.0](https://github.com/anoma/namada/releases/tag/v1.0.0)** by your preferred method (from source, precompiled binaries). Refer to the docs for [installation instructions](https://docs.namada.net/introduction/install).

2. (Optional) By default, Namada will store its data in `$HOME/.local/share/namada` on Ubuntu systems. This is called the 'base directory'. For instructions on setting a different base directory, see [here](https://docs.namada.net/operators/ledger/base-directory). To check the default base directory on your OS, use `namadac utils default-base-dir`. 

3. Set the following environment variables  
```
export NAMADA_NETWORK_CONFIGS_SERVER="https://github.com/anoma/namada-mainnet-genesis/releases/download/mainnet-genesis"
export VALIDATOR_ALIAS=<your-validator-alias> 
export CHAIN_ID=namada.5f5de2dd1b88cba30586420
```

4. Copy your pre-genesis `validator-wallet.toml` into the following location, creating the directory if necessary:  
```$BASE_DIR/pre-genesis/$VALIDATOR_ALIAS/validator-wallet.toml```  
**Note:** on Ubuntu, this corresponds to  
```~/.local/share/namada/pre-genesis/$VALIDATOR_ALIAS/validator-wallet.toml```

5. Initialize your node:  
```
namadac utils join-network --chain-id $CHAIN_ID --genesis-validator $VALIDATOR_ALIAS
```

6. Add some persistent peers to your `config.toml` file. First, select from the published list of peers at the bottom of this page. Then, open your node's configuration located at `$BASE_DIR/$CHAIN_ID/config.toml` and find the field `persistent_peers` (which should be empty). Add peers in the format `tcp://<node id>@<IP address>:<port>` separated by commas. Aim to add about 10 persistent peers to your config.

**Example on Ubuntu:**
In the file `~/.local/share/namada/$CHAIN_ID/config.toml`
Add peers following this format (you can contribute your peers with the instructions found at the bottom of this page):
```
persistent_peers = "tcp://05309c2cce2d163027a47c662066907e89cd6b99@104.251.123.123:26656,tcp://54386c1252ecabe5ba1fae2f083b37ca5ebd57dc@192.64.82.62:26656,tcp://2bf5cdd25975c239e8feb68153d69c5eec004fdb@64.118.250.82:46656"
```
This can be done by executing the following examle command (replace addresses with your actual desired peers):
```bash
sed -i 's#persistent_peers = ".*"#persistent_peers = "'\
'tcp://05309c2cce2d163027a47c662066907e89cd6b99@104.251.123.123:26656,'\
'tcp://54386c1252ecabe5ba1fae2f083b37ca5ebd57dc@192.64.82.62:26656,'\
'tcp://2bf5cdd25975c239e8feb68153d69c5eec004fdb@64.118.250.82:46656'\
'"#' $HOME/.local/share/namada/namada.5f5de2dd1b88cba30586420/config.toml
```

7. Start *before genesis time* and leave it running -- at genesis time, it will become active. Start your node using the command  
```namadan ledger run```
**Note: for instructions on running your node as a `systemd service`, see [here](https://docs.namada.net/operators/ledger/running-a-full-node#running-the-namada-ledger-as-a-systemd-service)**
After the initial startup, you should see in the logs:  
```Waiting for ledger genesis time: DateTimeUtc(2024-12-03T15:00:00Z)```
If your node is correctly configured as a genesis validator, you should also see:
```This node is a validator.```

8. At genesis time, once enough voting power is online, you should begin to see new blocks in your node's logs.


### Instructions for full nodes:
1. Same as above
2. Same as above
3. `export NAMADA_NETWORK_CONFIGS_SERVER` and `export CHAIN_ID` only
4. Skip this step
5. Omit the `--genesis-validator` argument:  
```namadac utils join-network --chain-id $CHAIN_ID```
6. Same as above
7. Same as above, except you should see  
```This node is not a validator.```

### Instructions for users without running a node:
Follow the same steps as for a full node, with the last required step being `namadac utils join-network --chain-id $CHAIN_ID`. You do not need to run a node or configure any peers.

### Share your seed node or peer address
Sharing is caring ❤️. If you want to share your seed node or peer address, please open a PR to this repo with an entry in the [README](./README.md) under either the `Seed nodes` or `Peers` section!
In order to do this, you must provide your node-id, which can be done with the following command (must be run *after* starting your node):  
```
NODE_ID=$(cometbft show-node-id --home $HOME/.local/share/namada/$CHAIN_ID/cometbft/ | awk '{last_line = $0} END {print last_line}')
echo $NODE_ID
```

### Additional docs resources:
- [Node configuration reference](https://docs.namada.net/operators/ledger/env-vars)
- [`systemd` service file example](https://docs.namada.net/operators/ledger/running-a-full-node#running-the-namada-ledger-as-a-systemd-service)
- [Operator reference](https://docs.namada.net/operators)