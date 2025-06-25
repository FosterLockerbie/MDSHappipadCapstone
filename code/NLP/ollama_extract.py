import pandas as pd
import subprocess
import json
from tqdm import tqdm

# Step 1: Define function to query Ollama
def query_ollama(prompt: str, model: str = "mistral") -> str:
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.stdout.decode().strip()

# Step 2: Extract structured info from one listing (title + description)
def extract_info_from_text(text: str) -> dict:
    prompt = f"""
You are a rental listing extractor. You will receive one rental listing description.
Extract structured information and return it as a **JSON object** with the following flat schema.
If a field is missing or unclear, use "unknown" or leave it empty.

Schema:
{{
  "number_of_people": "integer or 'unknown'",
  "bedrooms": "integer or 'unknown'",
  "pets_allowed": "true, false, or 'unknown'",
  "property_size": "'small', 'medium', 'large', or 'unknown'",
  "shared_spaces": "comma-separated string or 'unknown'",
  "bathroom_type": "'private', 'shared', or 'unknown'",
  "nearby_amenities": "comma-separated string from [bus, store, recreation centre/pool, school and university] or 'unknown'",
  "unique_features": "semicolon-separated string or 'unknown'"
}}

Input listing:
\"{text}\"

Instructions:
- All other fields should be inferred or filled with "unknown" if not present.
- Output only a **valid JSON object**, with no surrounding text or explanation.
    """

    try:
        response = query_ollama(prompt)
        return json.loads(response.strip())
    except Exception:
        return {
            "number_of_people": "unknown",
            "bedrooms": "unknown",
            "pets_allowed": "unknown",
            "property_size": "unknown",
            "shared_spaces": "unknown",
            "bathroom_type": "unknown",
            "nearby_amenities": "unknown",
            "unique_features": "unknown"
        }

# Step 3: Load dataset
df = pd.read_csv("nlp_text_contracts.csv")  

# Step 4: Combine 'title' and 'description' as text input
df["text_input"] = df["Property Title"].fillna('') + ". " + df["Description"].fillna('')

# Step 5: Loop through each row and extract structured info
results = []
for text in tqdm(df["text_input"], desc="Extracting info"):
    results.append(extract_info_from_text(text))

# Step 6: Append extracted results to DataFrame
structured_df = pd.DataFrame(results)
df = pd.concat([df, structured_df], axis=1)

# Step 7: Save to new CSV
df.to_csv("extracted_contracts.csv", index=False)
print("Extraction complete! Saved to extracted_contracts.csv")