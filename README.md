---

## 🧠 Continued Pre-training of Large Language Models

This repository contains research code and experiments focused on **continued pre-training** of transformer-based language models.
The objective is to enhance model performance on **domain-specific data** while maintaining general language understanding.

---

### 🚀 Project Overview

Continued pre-training (CPT) extends a base large language model (LLM) using new corpora to:

* Improve **domain adaptation** and contextual awareness.
* Reduce performance gaps on **specialized downstream tasks**.
* Preserve **general reasoning ability** through controlled fine-tuning.

---

### ⚙️ Key Features

* Support for **transformer-based models** (e.g., GPT, LLaMA, RoBERTa).
* Modular pipeline for **data ingestion, tokenization, and chunking**.
* Integration with **Hugging Face Transformers**, **PEFT (LoRA)**, and **bitsandbytes** for efficient training.
* **WANDB logging** for experiment tracking.
* Environment management with `.env` and `python-dotenv`.

---

### 📦 Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/continued-pretraining.git
cd continued-pretraining
pip install -r requirements.txt
```

---

### 🧩 Requirements

See [`requirements.txt`](./requirements.txt) for full dependencies.
Key libraries include:

* `transformers`
* `datasets`
* `peft`
* `bitsandbytes`
* `python-dotenv`
* `wandb`

---

### 🧪 Usage

Example Colab setup for continued pre-training:

```python
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model

# Load dataset and model
dataset = load_dataset("path/to/your/dataset")
tokenizer = AutoTokenizer.from_pretrained("model_name")
model = AutoModelForCausalLM.from_pretrained("model_name")

# Configure LoRA
lora_config = LoraConfig(r=8, lora_alpha=32, target_modules=["q_proj", "v_proj"])
model = get_peft_model(model, lora_config)

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=2,
    learning_rate=2e-5,
    num_train_epochs=3,
    logging_dir="./logs",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"]
)

trainer.train()
```

---

### 🧭 Project Structure

```
continued-pretraining/
├── notebooks/          # Colab or Jupyter notebooks
├── requirements.txt
└── README.md
```

---

### 📊 Experiment Tracking

This project integrates with **Weights & Biases (WANDB)** for logging:

```bash
wandb login
```

Make sure your `.env` file contains:

```
WANDB_API_KEY=your_api_key
```

---

### 📚 Citation

If you use this repository or adapt its methods, please cite or acknowledge this work appropriately.

---

### 🧑‍🔬 Author

**Taqiyudin Miftah Adn**
Department of Computer Engineering
Faculty of Computer Science

---

