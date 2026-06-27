"""LLM-agnostic client — any OpenAI-compatible /chat/completions endpoint.

Works with OpenAI, Together, Groq, OpenRouter, Mistral, local Ollama/LM Studio, etc.
Just point `base_url` at the provider and set the right `api_key_env` (none for local).
"""
import os, json, time, urllib.request, urllib.error

RETRY_STATUS = {429, 500, 502, 503, 504}


def chat(messages, llm, retries=3):
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
    last = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in RETRY_STATUS and attempt < retries:
                time.sleep(5 * attempt); continue
            raise SystemExit(f"LLM call failed (HTTP {e.code}): "
                             f"{e.read().decode(errors='replace')[:400]}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            if attempt < retries:
                time.sleep(5 * attempt); continue
            raise SystemExit(f"LLM call failed (network): {last}")
