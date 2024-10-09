// convertBalances.js

const fs = require("fs");

async function fetchBalancesAndConvert() {
  try {
    // URL of the balances.toml file
    const url =
      "https://raw.githubusercontent.com/anoma/namada-mainnet-genesis/main/genesis/balances.toml";

    // Fetch the data from the URL
    const response = await fetch(url);
    let data = await response.text();

    // Remove comments from the data
    data = data.replace(/#.*$/gm, "").trim();

    // Split data into lines
    const lines = data.split("\n");

    // Initialize an object to hold key-value pairs
    const balances = {};

    // Process each line
    for (let line of lines) {
      // Trim whitespace from the line
      line = line.trim();

      // Skip empty lines
      if (line.length === 0) continue;

      // Split the line at the first '=' character
      const [rawKey, rawValue] = line.split("=");

      if (!rawKey || !rawValue) {
        console.warn(`Skipping invalid line: ${line}`);
        continue;
      }

      // Trim whitespace and quotes from key and value
      const key = rawKey.trim().replace(/^"|"$/g, "");
      const value = rawValue.trim().replace(/^"|"$/g, "");

      // Add the key-value pair to the balances object
      balances[key] = value;
    }

    // Convert the balances object to JSON
    const jsonData = JSON.stringify(balances, null, 2);

    // Write the JSON data to balances.json
    fs.writeFileSync("balances.json", jsonData, "utf8");

    console.log("balances.json has been created successfully.");
  } catch (error) {
    console.error("Error:", error);
  }
}

fetchBalancesAndConvert();
