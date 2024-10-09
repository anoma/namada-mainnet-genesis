// index.js

const toml = require("toml");
const fs = require("fs");

const owner = "anoma";
const repo = "namada-mainnet-genesis";
const path = "transactions";
const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;

async function fetchRepoFiles() {
  const response = await fetch(apiUrl);
  return await response.json();
}

async function processBondFiles(files) {
  // Step 3: Fetch and process all TOML files in parallel
  const dataArray = await Promise.all(
    files.map(async (file) => {
      try {
        const fileResponse = await fetch(file.download_url);
        const fileContent = await fileResponse.text();

        // Parse TOML content
        const data = toml.parse(fileContent);
        return data.bond;
      } catch (error) {
        console.error(`Error processing file ${file.name}:`, error);
        return null; // Skip this file
      }
    })
  );

  // Filter out null entries (files that had errors)
  const filteredDataArray = dataArray.filter((data) => data !== null);
  return filteredDataArray;
}

async function fetchFiles() {
  try {
    // Step 1: Get the list of files in the directory
    const files = await fetchRepoFiles();
    // Step 2: Filter files ending with '-bond.toml'
    const bondFiles = files.filter((file) => file.name.endsWith("-bond.toml"));

    // Step 3: Fetch and process all TOML files in parallel
    const bonds = await processBondFiles(bondFiles);
    const bondArray = bonds.flatMap(x => x)

    // Step 4: Write combined data to a JSON file
    fs.writeFileSync(
      "combined_bond_data.json",
      JSON.stringify(bondArray, null, 2)
    );

    console.log("Combined data written to combined_bond_data.json");
  } catch (error) {
    console.error("Error:", error);
  }
}

fetchFiles();
