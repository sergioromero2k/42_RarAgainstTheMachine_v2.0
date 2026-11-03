"""Answer generation with a small local model (Qwen3-0.6B)."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.models import MinimalSource

MODEL_NAME = "Qwen/Qwen3-0.6B"
MAX_CONTEXT_TOKENS = 3000
MAX_NEW_TOKENS = 200
SYSTEM_PROMPT = (
    "You answer questions about the vLLM codebase and documentation. "
    "Use only the provided context. If the context does not contain "
    "the answer, say that you do not know. Be concise."
)


def read_source_text(source: MinimalSource) -> str:
    """Return the text of the file region a source points to."""
    with open(source.file_path, "r") as f:
        content = f.read()
    return content[source.first_character_index:source.last_character_index]


class Generator:
    """Builds a prompt from retrieved sources and generates an answer."""

    def __init__(self, model_name: str = MODEL_NAME,
                 max_context_tokens: int = MAX_CONTEXT_TOKENS,
                 max_new_tokens: int = MAX_NEW_TOKENS) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.eval()
        self.max_context_tokens = max_context_tokens
        self.max_new_tokens = max_new_tokens

    def build_context(self, sources: list[MinimalSource]) -> str:
        """Join source texts, best first, within the token budget."""
        parts: list[str] = []
        used = 0
        for number, source in enumerate(sources, start=1):
            block = (f"[{number}] {source.file_path}\n"
                     f"{read_source_text(source)}\n")
            ids = self.tokenizer(block)["input_ids"]
            if used + len(ids) > self.max_context_tokens:
                if not parts:
                    parts.append(self.tokenizer.decode(
                        ids[:self.max_context_tokens]))
                break
            parts.append(block)
            used += len(ids)
        return "\n".join(parts)

    def answer(self, question: str, sources: list[MinimalSource]) -> str:
        """Generate an answer to the question grounded in the sources."""
        context = self.build_context(sources)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=False)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            output = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens,
                do_sample=False)
        new_tokens = output[0][inputs["input_ids"].shape[1]:]
        text: str = self.tokenizer.decode(
            new_tokens, skip_special_tokens=True)
        return text.strip()