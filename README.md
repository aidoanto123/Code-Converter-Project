# 🐍 Python → C++ Converter

A simple Gradio app that converts Python code into high-performance C++ using either **GPT** or **Claude**.  
You can also run your Python or C++ code directly inside the app and see the results.

---

## ✨ Features
- Convert Python code to optimized C++.
- Choose between **GPT** or **Claude** as the model.
- Run Python code instantly.
- Run C++ code instantly.
- Clean UI with colored input/output boxes.

---

## 🖼️ UI Preview
- **Python output box** → light blue background  
- **C++ output box** → light green background  

---

## 🔑 API Keys (.env file)

To use the Python → C++ conversion, you need API keys for OpenAI (GPT) and Anthropic (Claude). The easiest way is to create a `.env` file in your project folder.

### 1. Create a `.env` file
Place it in the same directory as `main.py`.

### 2. Add your API keys
```env
OPENAI_API_KEY="your_openai_key_here"
ANTHROPIC_API_KEY="your_anthropic_key_here"
```

### 3. Install `python-dotenv` (if your app doesn’t already load `.env`)
```bash
pip install python-dotenv
```

### 4. Load the keys in your Python code
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
````


---

## 📦 Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/aidoanto123/Code-Converter-Project.git
cd Code-Converter-Project
pip install -r requirements.txt
```

## ▶️ Usage

Run the app with:

```bash
python main.py

