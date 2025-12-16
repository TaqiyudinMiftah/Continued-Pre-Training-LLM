from huggingface_hub import (
    HfApi,
    create_repo,
    upload_file
)
import os

HF_TOKEN = os.getenv("HF_TOKEN")
assert HF_TOKEN is not None, "HF_TOKEN belum diset!"

REPO_ID = "aitfindonesia/Bakti-8B-Base"

api = HfApi(token=HF_TOKEN)

# 1. Buat repo (aman walau sudah ada)
create_repo(
    repo_id=REPO_ID,
    repo_type="model",
    exist_ok=True,
    private=False   # ubah True jika ingin private
)

# 2. Upload README.md
upload_file(
    path_or_fileobj="README.md",
    path_in_repo="README.md",
    repo_id=REPO_ID,
    repo_type="model",
    commit_message="Add initial README for Bakti-8B-Base"
)

print("✅ README berhasil di-push ke Hugging Face!")
