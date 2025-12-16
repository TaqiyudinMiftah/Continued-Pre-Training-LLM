import json
import os

DATASET_PATH = r"C:\Adn\Adn Belajar python\Continued Pre-Training LLM\Cleaning\pdf\clean\dataset.jsonl"
OUTPUT_DIR = r"C:\Adn\Adn Belajar python\Continued Pre-Training LLM\Cleaning\pdf\clean\markdown"

def save_as_markdown():
    """Convert dataset.jsonl to individual markdown files"""
    # Create output directory if not exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    count = 0
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            source = data["source"]
            text = data["text"]
            
            # Create markdown filename from source (replace .pdf with .md)
            md_filename = os.path.splitext(source)[0] + ".md"
            md_path = os.path.join(OUTPUT_DIR, md_filename)
            
            # Save markdown file
            with open(md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(text)
            
            count += 1
            print(f"Saved: {md_filename}")
    
    print(f"\nDone! {count} markdown file(s) saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    save_as_markdown()
