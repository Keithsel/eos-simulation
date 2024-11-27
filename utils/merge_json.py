import os
import json
import pandas as pd
import shutil
from pathlib import Path

def merge_json_to_csv(json_folder, subject_code):
    Path("data/bank").mkdir(parents=True, exist_ok=True)
    Path("proc/done").mkdir(parents=True, exist_ok=True)
    
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    processed_files = [f for f in os.listdir("proc/done") if f.endswith('.json')]
    
    new_files = [f for f in json_files if f not in processed_files]
    
    if not new_files:
        print("No new files to process")
        return
        
    all_questions = []
    for file in new_files:
        with open(os.path.join(json_folder, file), 'r') as f:
            all_questions.extend(json.load(f))
    
    new_df = pd.DataFrame(all_questions)
    
    csv_path = f"data/bank/{subject_code}.csv"
    
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        new_df = new_df[~new_df['question'].isin(existing_df['question'])]
        if len(new_df) == 0:
            print("No new questions to add")
            return
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df
    
    final_df.to_csv(csv_path, index=False)
    
    for file in new_files:
        shutil.copy2(
            os.path.join(json_folder, file),
            os.path.join("proc/done", file)
        )
    
    print(f"Processed {len(new_files)} files")
    print(f"Added {len(new_df)} questions to {csv_path}")

if __name__ == "__main__":
    merge_json_to_csv("proc/new", "SWE201c")
