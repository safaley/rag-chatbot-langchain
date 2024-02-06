const { spawn } = require("child_process");

function runPythonScript(queryText) {
  return new Promise((resolve, reject) => {
    // Run the Python script asynchronously
    const pythonProcess = spawn("python3", ["query_data.py", queryText]);

    let result = "";

    pythonProcess.stdout.on("data", (data) => {
      result += data.toString();
    });

    pythonProcess.on("close", (code) => {
      if (code === 0) {
        // Resolve the promise with the captured output
        resolve(result.trim());
      } else {
        // Reject the promise with an error message
        reject(new Error(`Python script exited with code ${code}`));
      }
    });
  });
}

// Example usage:
async function main() {
  const queryText = "Who is Alice";

  try {
    const response = await runPythonScript(queryText);
    console.log(response);
  } catch (error) {
    console.error(error.message);
  }
}

main();
