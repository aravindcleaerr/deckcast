"""LLM-agnostic client — any OpenAI-compatible /chat/completions endpoint.

Works with OpenAI, Together, Groq, OpenRouter, Mistral, local Ollama/LM Studio, etc.
Just point `base_url` at the provider and set the right `api_key_env` (none for local).
"""
import os, json, urllib.request, urllib.error


def chat(messages, llm):
    base = llm["base_url"].rstrip("/")
    key = os.environ.get(llm.get("api_key_env", ""), "")
    payload = {
        "model": llm["model"],
        "messages": messages,
        "temperature": llm.get("temperature", 0.7),
    }
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(base + "/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"LLM call failed (HTTP {e.code}): {e.read().decode(errors='replace')[:400]}")
    return data["choices"][0]["message"]["content"]
