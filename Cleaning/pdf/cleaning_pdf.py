import os
import glob
import json
import re
import pymupdf4llm
from tqdm import tqdm
from pathlib import Path

INPUT_FOLDER = r"C:\Adn\Adn Belajar python\Continued Pre-Training LLM\Cleaning\pdf\raw"
OUTPUT_FOLDER = r"C:\Adn\Adn Belajar python\Continued Pre-Training LLM\Cleaning\pdf\clean"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "dataset.jsonl")
MIN_LENGTH = 50

def clean_markdown_content(text):
    if not text:
        return ""
    
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    return text.strip()

def process_pdfs_to_jsonl(input_dir, output_path):
    # Buat folder output jika belum ada
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Buat folder input jika belum ada
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Folder '{input_dir}' dibuat. Silakan masukkan file PDF ke dalamnya.")
        return

    # Cari semua file PDF
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"Tidak ada file PDF ditemukan di folder '{input_dir}'.")
        return

    print(f"Ditemukan {len(pdf_files)} file PDF. Memulai konversi...")

    # Buka file output JSONL
    with open(output_path, 'w', encoding='utf-8') as f_out:
        
        # Loop dengan progress bar
        for pdf_path in tqdm(pdf_files, desc="Processing"):
            try:
                filename = os.path.basename(pdf_path)
                
                # --- CORE PROCESS: Convert PDF to Markdown ---
                # pymupdf4llm sangat bagus mendeteksi Header, Bold, dan Tabel
                md_text = pymupdf4llm.to_markdown(pdf_path)
                
                # --- CLEANING ---
                cleaned_text = clean_markdown_content(md_text)

                # Skip jika hasil convert kosong atau terlalu pendek
                if len(cleaned_text) < MIN_LENGTH:
                    continue

                # --- FORMATTING KE JSONL ---
                # Struktur ini umum digunakan untuk CPT
                entry = {
                    "source": filename,
                    "text": cleaned_text
                }

                # Tulis ke file (one json object per line)
                json.dump(entry, f_out, ensure_ascii=False)
                f_out.write('\n')

            except Exception as e:
                print(f"\n[ERROR] Gagal memproses {pdf_path}: {e}")

    print(f"\nSelesai! Dataset tersimpan di: {output_path}")
    print("Format siap digunakan untuk HuggingFace / Axolotl / LLaMA-Factory.")

if __name__ == "__main__":
    process_pdfs_to_jsonl(INPUT_FOLDER, OUTPUT_FILE)