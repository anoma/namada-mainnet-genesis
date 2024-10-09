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

async function processValidatorFiles(files) {
  // Step 3: Fetch and process all TOML files in parallel
  const dataArray = await Promise.all(
    files.map(async (file) => {
      try {
        const fileResponse = await fetch(file.download_url);
        const fileContent = await fileResponse.text();

        // Parse TOML content
        const data = toml.parse(fileContent);

        // Remove the 'established_account' section
        delete data.established_account;

        // Extract the filename without extension to use as validator_name
        const fileName = file.name;
        const validatorName = fileName.replace("-validator.toml", "");

        // Add validator_name to the validator_account section
        if (Array.isArray(data.validator_account)) {
          data.validator_account.forEach((account) => {
            account.validator_name = validatorName;
          });
        } else if (
          data.validator_account &&
          typeof data.validator_account === "object"
        ) {
          data.validator_account.validator_name = validatorName;
        } else {
          console.warn(
            `validator_account is missing or not in expected format in file: ${file.name}`
          );
        }

        return data;
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
    // Step 2: Filter files ending with '-validator.toml'
    const validatorFiles = files.filter((file) =>
      file.name.endsWith("-validator.toml")
    );

    // Step 3: Fetch and process all TOML files in parallel
    const validatorArray = await processValidatorFiles(validatorFiles);
    
    // Step 4: Write combined data to a JSON file
    fs.writeFileSync(
      "combined_validator_data.json",
      JSON.stringify(validatorArray, null, 2)
    );

    console.log("Combined data written to combined_validator_data.json");
  } catch (error) {
    console.error("Error:", error);
  }
}

fetchFiles();
