import os
from pathlib import Path

from .prompt_template import SYSTEM_PROMPT, user_prompt

class LocalLlmEngine:
    def __init__(self):
        self.model = None
        self.error = None
        self.model_path = Path(
            os.getenv("MODEL_PATH", "/app/models/qwen2.5-0.5b-instruct-q4_k_m.gguf")
        )

    @property
    def available(self):
        return self.model is not None

    def load(self):
        if not self.model_path.is_file():
            self.error = f"Model not found at {self.model_path}"
            return
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=int(os.getenv("LLM_CONTEXT_TOKENS", "2048")),
                n_threads=int(os.getenv("LLM_THREADS", "2")),
                n_gpu_layers=0,
                chat_format="chatml",
                verbose=False,
            )
        except Exception as exc:
            self.error = f"Unable to load GGUF: {exc}"

    def generate(self, query, candidates, current_time):
        if not self.model:
            raise RuntimeError("Local model is unavailable")
        result = self.model.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(query, candidates, current_time)},
            ],
            temperature=0.1,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "120")),
        )
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM returned empty text")
        return content.strip()
