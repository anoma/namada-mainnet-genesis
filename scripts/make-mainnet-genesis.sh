#!/bin/bash

REPO="anoma/namada"
RELEASE="latest"
OUTPUT_FILE="binaries.tar.gz"
EXTRACT_DIR="binaries"

OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" == "Linux" && "$ARCH" == "x86_64" ]]; then
    FILE_NAME="namada-v1.0.0-Linux-x86_64.tar.gz"
    TARGET_FILE="namada-v1.0.0-Linux-x86_64/namadac"
elif [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    FILE_NAME="namada-v1.0.0-Darwin-arm64.tar.gz"
    TARGET_FILE="namada-v1.0.0-Darwin-arm64/namadac"
else
    echo "Error: Unsupported OS or architecture ($OS-$ARCH)."
    exit 1
fi

URL="https://github.com/$REPO/releases/$RELEASE/download/$FILE_NAME"
echo "Downloading $FILE_NAME from $URL..."
curl -L -o "$OUTPUT_FILE" "$URL"

# Verify the download
if [[ $? -eq 0 ]]; then
    echo "File downloaded successfully: $OUTPUT_FILE"
else
    echo "Error: Failed to download the file."
    exit 1
fi

# Extract the specific file
mkdir -p "$EXTRACT_DIR"
echo "Extracting $TARGET_FILE from $OUTPUT_FILE to $EXTRACT_DIR..."
tar --strip-components=1 -xzf "$OUTPUT_FILE" -C "$EXTRACT_DIR" "$TARGET_FILE"

# Verify extraction
if [[ $? -eq 0 ]]; then
    echo "Extraction completed successfully. $TARGET_FILE is in $EXTRACT_DIR."
    rm $OUTPUT_FILE
else
    echo "Error: Failed to extract $TARGET_FILE. Ensure the file exists in the archive."
    rm $OUTPUT_FILE
    exit 1
fi

GENESIS_TEMPLATE_PATH="genesis"
WASM_DIR="wasm"
WASM_CHECKSUMS_PATH="$WASM_DIR/checksums.json"

TIMEOUT_CONSENSUS_COMMIT="6s"
CHAIN_PREFIX="namada"
GENESIS_TIME="2024-12-3T15:00:00.000000000+00:00"

echo "Building genesis files..."

./binaries/namadac utils init-network --templates-path $GENESIS_TEMPLATE_PATH --wasm-dir $WASM_DIR --consensus-timeout-commit $TIMEOUT_CONSENSUS_COMMIT --wasm-checksums-path $WASM_CHECKSUMS_PATH --chain-prefix $CHAIN_PREFIX  --genesis-time $GENESIS_TIME

CHECKSUM="5f5de2dd1b88cba30586420"
FILE="namada.$CHECKSUM.tar.gz"

if [ -e "$FILE" ]; then
    echo "Genesis file correctly created."
    rm -rf "binaries"
    exit 0
else 
    echo "Genesis file invalid."
    rm -rf "binaries"
    exit 1
fi