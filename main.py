import os
import io
import sys
from typing import Generator, Iterable
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
import gradio as gr
import platform
import subprocess

load_dotenv(override=True)
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "your-key-if-not-using-env"))
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", "your-key-if-not-using-env"))

openai_client = OpenAI()
claude_client = anthropic.Anthropic()

OPENAI_MODEL = "gpt-4o"
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"

SYSTEM_MESSAGE = (
    "You are an assistant that reimplements Python code in high performance C++ for cross-platform systems. "
    "Respond only with C++ code; use comments sparingly and do not provide any explanation other than occasional comments. "
    "The C++ response needs to produce an identical output in the fastest possible time. Keep implementations of random number generators identical so that results match exactly."
)

def user_prompt_for(python_code: str):
    return (
        "Rewrite this Python code in C++ with the fastest possible implementation that produces identical output in the least time. "
        "Respond only with C++ code; do not explain your work other than a few comments. "
        "Pay attention to number types to ensure no int overflows. Remember to #include all necessary C++ headers such as <iomanip>.\n\n"
        + python_code
    )

def messages_for(python_code: str):
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": user_prompt_for(python_code)},
    ]


def write_output(cpp: str, path: str = "optimized.cpp"):
    code = cpp.replace("```cpp", "").replace("```", "")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

def stream_gpt(python_code: str):
    stream = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages_for(python_code),
        stream=True,
    )
    reply = ""
    for chunk in stream:
        fragment = chunk.choices[0].delta.content or ""
        reply += fragment
        yield reply.replace("```cpp\n", "").replace("```", "")

def stream_claude(python_code: str):
    result = claude_client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_MESSAGE,
        messages=[{"role": "user", "content": user_prompt_for(python_code)}],
    )
    reply = ""
    with result as s:
        for text in s.text_stream:
            reply += text
            yield reply.replace("```cpp\n", "").replace("```", "")

def optimize(python_code: str, model: str):
    if model == "GPT":
        generator = stream_gpt(python_code)
    elif model == "Claude":
        generator = stream_claude(python_code)
    else:
        raise ValueError("Unknown model selection")
    for partial in generator:
        yield partial

PYTHON_HARD = """# Be careful to support large number sizes
def lcg(seed, a=1664525, c=1013904223, m=2**32):
    value = seed
    while True:
        value = (a * value + c) % m
        yield value

def max_subarray_sum(n, seed, min_val, max_val):
    lcg_gen = lcg(seed)
    random_numbers = [next(lcg_gen) % (max_val - min_val + 1) + min_val for _ in range(n)]
    max_sum = float('-inf')
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += random_numbers[j]
            if current_sum > max_sum:
                max_sum = current_sum
    return max_sum

def total_max_subarray_sum(n, initial_seed, min_val, max_val):
    total_sum = 0
    lcg_gen = lcg(initial_seed)
    for _ in range(20):
        seed = next(lcg_gen)
        total_sum += max_subarray_sum(n, seed, min_val, max_val)
    return total_sum

n = 10000
initial_seed = 42
min_val = -10
max_val = 10

import time
start_time = time.time()
result = total_max_subarray_sum(n, initial_seed, min_val, max_val)
end_time = time.time()

print("Total Maximum Subarray Sum (20 runs):", result)
print("Execution Time: {:.6f} seconds".format(end_time - start_time))
"""

def execute_python(code: str):
    old_stdout = sys.stdout
    output = io.StringIO()
    try:
        sys.stdout = output
        sandbox_globals = {"__name__": "__main__"}
        exec(code, sandbox_globals)
    except Exception as e:
        print(f"Python execution error: {e}")
    finally:
        sys.stdout = old_stdout
    return output.getvalue()

def _find_compiler():
    if platform.system().lower().startswith("win"):
        return "g++"  # Use MSYS2 g++ on Windows
    else:
        for candidate in ("g++", "clang++"):
            try:
                subprocess.run([candidate, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return candidate
            except Exception:
                continue
        raise RuntimeError("No suitable C++ compiler found.")

def execute_cpp(code: str):
    write_output(code)
    try:
        compiler = _find_compiler()
        exe_name = "optimized.exe" if platform.system().lower().startswith("win") else "optimized"
        compile_cmd = [compiler, "-O3", "-std=c++17", "-o", exe_name, "optimized.cpp"]
        compile_proc = subprocess.run(compile_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        if compile_proc.returncode != 0:
            return f"Compilation failed with {compiler}:\n{compile_proc.stderr}"
        run_cmd = [exe_name] if platform.system().lower().startswith("win") else [f"./{exe_name}"]
        run_proc = subprocess.run(run_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        if run_proc.returncode != 0:
            return f"Program crashed:\n{run_proc.stderr}"
        return run_proc.stdout
    except Exception as e:
        return f"An error occurred: {e}"


CSS = """
#python_box {
    background-color: #93c5fd !important; /* medium blue */
    color: #000000 !important;           /* black text */
}

#cpp_box {
    background-color: #6ee7b7 !important; /* medium green */
    color: #000000 !important;            /* black text */
}
"""


with gr.Blocks(css=CSS, title="Python → C++ Converter") as ui:
    gr.Markdown("## Convert Python to high‑performance C++ (OpenAI / Anthropic)")
    with gr.Row():
        python_box = gr.Textbox(label="Python code", lines=16)
        cpp_box = gr.Textbox(label="C++ code", lines=16)
    with gr.Row():
        model_dd = gr.Dropdown(["GPT", "Claude"], label="Select model", value="GPT")
    with gr.Row():
        convert_btn = gr.Button("Convert code")
        run_py_btn = gr.Button("Run Python")
        run_cpp_btn = gr.Button("Run C++")
    with gr.Row():
        py_out = gr.Textbox(label="Python result", lines=8, elem_id="python_box")
        cpp_out = gr.Textbox(label="C++ result", lines=8, elem_id="cpp_box")

    convert_btn.click(fn=optimize, inputs=[python_box, model_dd], outputs=[cpp_box])
    run_py_btn.click(fn=execute_python, inputs=[python_box], outputs=[py_out])
    run_cpp_btn.click(fn=execute_cpp, inputs=[cpp_box], outputs=[cpp_out])

if __name__ == "__main__":
    ui.launch(inbrowser=True)

