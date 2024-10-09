// fetchValidatorsData.js

const fs = require("fs");

async function fetchValidatorsData() {
  try {
    // Step 1: Fetch the README.md content
    const rawUrl =
      "https://raw.githubusercontent.com/anoma/namada-mainnet-genesis/main/README.md";
    const response = await fetch(rawUrl);
    const content = await response.text();

    // Step 2: Extract the Validators section
    const validatorsSection = content.split("## Validators")[1];
    if (!validatorsSection) {
      throw new Error("Validators section not found in README.md");
    }

    // Split the validatorsSection into individual validator entries
    const validatorEntries = validatorsSection.split("- address:").slice(1);

    // Step 3: Process each validator entry
    const validatorsData = validatorEntries.map((entry) => {
      // Prepare an object to hold the validator data
      const validator = {};

      // Since each entry is indented with spaces, we can use regex to extract
      const lines = entry.split("\n");

      // The first line is the address
      const addressLine = lines[0].trim();
      const addressMatch = addressLine.match(/`([^`]+)`/);
      if (addressMatch) {
        validator.address = addressMatch[1].trim();
      }

      // Process the subsequent lines
      lines.slice(1).forEach((line) => {
        const trimmedLine = line.trim();
        const fieldMatch = trimmedLine.match(/- ([^:]+): `([^`]+)`/);
        if (fieldMatch) {
          const key = fieldMatch[1].toLowerCase().replace(/ /g, "_");
          let value = fieldMatch[2];

          // Special handling for percentage values
          if (value.endsWith("%")) {
            value = value.slice(0, -1);
          }

          // For total voting power, we need to split into two items
          if (key === "total_voting_power") {
            const totalVotingPowerMatch = value.match(
              /^([^ ]+) \(([^%]+)% of total voting power\)$/
            );
            if (totalVotingPowerMatch) {
              validator.total_bond = parseFloat(
                totalVotingPowerMatch[1].replace(/,/g, "")
              );
              validator.total_voting_power = parseFloat(
                totalVotingPowerMatch[2]
              );
            } else {
              console.warn(
                `Unexpected format for total voting power: ${value}`
              );
            }
          } else {
            validator[key] = value;
          }
        }
      });

      return validator;
    });

    // Step 4: Read combined_data.json and create a map of address to discord_handle
    const combinedData = JSON.parse(
      fs.readFileSync("combined_data.json", "utf8")
    );
    const addressToDiscord = {};

    combinedData.forEach((item) => {
      // Handle both array and object forms of validator_account
      const validatorAccounts = Array.isArray(item.validator_account)
        ? item.validator_account
        : [item.validator_account];
      validatorAccounts.forEach((account) => {
        if (account && account.address) {
          const address = account.address.trim().toLowerCase();

          let discordHandle = null;
          console.log(account.metadata, "metadata ayyy");
          // Access discord_handle from account.metadata.discord_handle
          if (account.metadata && account.metadata.discord_handle) {
            discordHandle = account.metadata.discord_handle;
          }

          // Map the normalized address to the discord_handle
          addressToDiscord[address] = discordHandle;
        }
      });
    });
    console.log(addressToDiscord, "address to discord");
    // Step 5: Add discord_handle to validatorsData
    validatorsData.forEach((validator) => {
      const address = validator.address.trim().toLowerCase();
      const discordHandle = addressToDiscord[address];
      if (discordHandle) {
        validator.discord_handle = discordHandle;
        console.log("discord added");
      } else {
        validator.discord_handle = null;
        console.warn(
          `Discord handle not found for address: ${validator.address}`
        );
      }
    });

    // Step 6: Write combined data to a JSON file
    fs.writeFileSync(
      "validators_data.json",
      JSON.stringify(validatorsData, null, 2)
    );

    console.log("Validators data written to validators_data.json");
  } catch (error) {
    console.error("Error:", error);
  }
}

fetchValidatorsData();
