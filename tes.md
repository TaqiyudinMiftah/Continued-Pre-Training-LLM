---

base_model: aitfindonesia/Bakat-8B-Base
library_name: peft
pipeline_tag: text-generation
language:

* id
  tags:
* base_model:Qwen/Qwen3-8B
* lora
* sft
* transformers
* trl
* lm-eval
* biawak
* indonesian
  license: apache-2.0
  datasets:
* internal-curated

---

# Bakti-8B-Base

## Model Details

### Model Description

**Bakti-8B-Base** adalah base model bahasa Indonesia yang dirancang untuk **Continued Pre-Training (CPT)** pada domain kebijakan dan pengawasan ruang digital. Model ini merupakan turunan dari **Biawak-8B-Base** dan dibangun di atas arsitektur **Qwen3-8B**, dengan pendekatan **LoRA (Low-Rank Adaptation)** dan **4-bit quantization** untuk efisiensi memori dan komputasi.

* **Developed by**: Tim 1 AITF
* **Model type**: Causal Language Model (LoRA Adapter)
* **Base architecture**: Qwen3-8B
* **Primary language**: Indonesian (id)
* **License**: Apache-2.0

---

## Training Data Composition

| Kategori         | Elemen                                                                                                | Jumlah Token (M) | Persentase |
| ---------------- | ----------------------------------------------------------------------------------------------------- | ---------------- | ---------- |
| **DTP**          | Okupasi PON TIK, Tren Pekerjaan, Kompetensi & SDM, Kebijakan & Regulasi DTP, Teknologi Digital Talent | 94               | 43.9%      |
| **PRD**          | Judi Online, Hoax, Perlindungan Anak, Konten Edukasi, Kebijakan & Regulasi PRD, Kekerasan Masyarakat  | 92               | 42.9%      |
| **Wikipedia ID** | Pengetahuan Umum & Bahasa Daerah Seluruh Indonesia                                                    | 28.2             | 13.2%      |
| **Total**        | –                                                                                                     | **214.2**        | **100%**   |

---

## Intended Use

### Direct Use (Recommended)

Model ini **ditujukan untuk Continued Pre-Training**, khususnya untuk:

* Adaptasi domain kebijakan publik dan regulasi digital
* Pengayaan pengetahuan spesifik Indonesia
* Pre-adaptation sebelum Instruction Tuning atau SFT

### Out-of-Scope Use

* **Long-context conversations** (belum dioptimalkan)
* **High-stakes decision making** (legal, medis, finansial)
* **Chat-oriented instruction following** tanpa fine-tuning lanjutan

---

## Bias, Risks, and Limitations

* Dataset didominasi oleh domain kebijakan dan pengawasan ruang digital, sehingga bias topikal dapat muncul pada domain non-terkait.
* Model belum melalui tahap preference alignment (RLHF/DPO).
* Konten Wikipedia digunakan sebagai penyeimbang, namun tidak menjamin netralitas penuh.

Pengguna disarankan melakukan evaluasi tambahan sebelum penggunaan produksi.

---

## Recommendations

* Gunakan **Qwen3 chat template** untuk hasil generasi terbaik.
* Lakukan **Instruction Fine-Tuning** atau **Preference Tuning** sebelum deployment ke end-user.
* Verifikasi keluaran model untuk informasi kritikal.

---

## How to Get Started

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Load base model
base_model_name = "ismaprasetiyadi/Biawak-8B-Base"
adapter_model_name = "aitfindonesia/Bakti-8B-Base"

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# Load tokenizer & adapter
tokenizer = AutoTokenizer.from_pretrained(adapter_model_name, trust_remote_code=True)
model = PeftModel.from_pretrained(model, adapter_model_name)

# Inference example
messages = [
    {"role": "user", "content": "Jelaskan sejarah singkat kemerdekaan Indonesia."}
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

---

## Training Details

### Training Data

* **Total size**: ~214M tokens
* **Domains**: Digital Talent Policy (DTP), Pengawasan Ruang Digital (PRD), Wikipedia Indonesia
* **Split**: Train (90%) / Validation (10%)

### Training Procedure

Model dilatih menggunakan **Continued Pre-Training (CPT)** dengan LoRA pada HuggingFace Transformers.

#### Hyperparameters

* **Precision**: bf16 (mixed precision)
* **Quantization**: 4-bit (nf4)
* **LoRA Rank (r)**: 8
* **LoRA Alpha**: 16
* **Target modules**: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
* **Batch size**: 4 / device
* **Gradient accumulation**: 16 (effective batch size = 32)
* **Learning rate**: 2e-4 (linear schedule)
* **Warmup ratio**: 0.03
* **Epochs**: 1
* **Optimizer**: adamw_8bit

---

## Evaluation

### Results

* **Final Training Loss**: ~1.2685
* **Final Validation Loss**: ~1.264
* **Training Perplexity**: ~3.56
* **Validation Perplexity**: ~3.55

### Benchmark (General)

* **MMLU**: ~74.20
* **IndoMMLU**: ~65.66
* **XCOPA-ID**: ~75.80

---

## Environmental Impact

Estimasi emisi karbon mengikuti metodologi Lacoste et al. (2019).

* **Hardware**: NVIDIA A100 80GB
* **Training time**: ~36 jam
* **Compute region**: Indonesia
* **Infrastructure**: University / Private Server

---

## Framework Versions

* Transformers: 4.x
* PyTorch: 2.x
* Datasets: 2.x
* Tokenizers: 0.x
