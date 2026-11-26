"""
repo_buddy — RAG analysis pipeline

    clone ─► load code files ─► chunk (with file + line labels)
          ─► embed (Gemini embedding API) ─► ChromaDB (in-memory)
          ─► retrieve top-k chunks for several security/architecture queries
          ─► one structured-JSON LLM call ─► report

Why RAG: a repo rarely fits in one prompt, and sending everything costs more
and dilutes the answer. Retrieval sends only the chunks most relevant to each
question. Embeddings use Gemini's hosted model, so the backend needs no
PyTorch / local model and fits on a small free-tier server.
"""
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL

# ── Tunables ─────────────────────────────────────
CHUNK_SIZE = 1000          # characters per chunk
CHUNK_OVERLAP = 200        # characters shared between neighbouring chunks
MAX_FILE_BYTES = 200_000   # skip huge/generated files
MAX_CHUNKS = 600           # cap embedding cost for very large repos
TOP_K = 8                  # chunks retrieved per query
EMBED_BATCH = 100          # texts per embedding request
EMBED_DIMS = 768           # smaller vectors = less memory, same ranking quality for this use

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".php",
    ".swift", ".kt", ".c", ".cpp", ".h", ".cs", ".scala", ".dart", ".lua",
    ".html", ".css", ".scss", ".vue", ".svelte",
    ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
    ".sh", ".bash", ".tf", ".sql", ".dockerfile",
}
CODE_FILENAMES = {"Dockerfile", ".env.example"}
EXCLUDED_DIRS = {
    "node_modules", "venv", ".venv", ".git", "__pycache__", "dist", "build",
    ".next", "vendor", "coverage", ".turbo",
}
EXCLUDED_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock"}

# Each query pulls TOP_K chunks from a different angle of the codebase.
RETRIEVAL_QUERIES = [
    "security vulnerabilities authentication authorization secrets API keys passwords",
    "architecture structure imports dependencies framework entry point",
    "database connections external API calls data flow user input",
    "error handling edge cases broken imports missing files configuration",
]


class AnalysisError(Exception):
    """A scan couldn't produce a real report; the message is shown to the user."""


@dataclass
class Chunk:
    path: str
    start_line: int
    end_line: int
    text: str

    def labelled(self) -> str:
        return f"### {self.path} (lines {self.start_line}-{self.end_line})\n{self.text}"


# ── 1. Load ──────────────────────────────────────

def load_code_files(repo_path: str) -> list[tuple[str, str]]:
    """Return [(relative_path, text)] for readable source/config files."""
    root = Path(repo_path)
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if name in EXCLUDED_FILES:
                continue
            if p.suffix.lower() not in CODE_EXTENSIONS and name not in CODE_FILENAMES:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if text.strip():
                files.append((p.relative_to(root).as_posix(), text))
    return sorted(files)


# ── 2. Chunk ─────────────────────────────────────

def chunk_file(path: str, text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[Chunk]:
    """Split text into overlapping windows, preferring to cut at line breaks."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            newline = text.rfind("\n", start + size // 2, end)
            if newline != -1:
                end = newline + 1
        piece = text[start:end]
        if piece.strip():
            start_line = text.count("\n", 0, start) + 1
            chunks.append(Chunk(path, start_line, start_line + piece.count("\n"), piece))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


# ── 3. Embed + index ─────────────────────────────

def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        result = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=texts[i:i + EMBED_BATCH],
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBED_DIMS),
        )
        vectors.extend(e.values for e in result.embeddings)
    return vectors


def retrieve_context(chunks: list[Chunk], queries: list[str] = RETRIEVAL_QUERIES, k: int = TOP_K) -> str:
    """Embed chunks into an in-memory ChromaDB collection and return the top-k per query."""
    import chromadb

    client = chromadb.EphemeralClient()
    collection = client.create_collection(f"scan-{uuid.uuid4().hex[:8]}", metadata={"hnsw:space": "cosine"})
    try:
        docs = [c.labelled() for c in chunks]
        collection.add(
            ids=[str(i) for i in range(len(docs))],
            documents=docs,
            embeddings=embed_texts(docs, "RETRIEVAL_DOCUMENT"),
        )
        query_vectors = embed_texts(queries, "RETRIEVAL_QUERY")
        hits = collection.query(query_embeddings=query_vectors, n_results=min(k, len(docs)))
        seen: dict[str, None] = {}
        for docs_for_query in hits["documents"]:
            for d in docs_for_query:
                seen.setdefault(d, None)  # de-duplicate, keep order
        return "\n\n---\n\n".join(seen)
    finally:
        client.delete_collection(collection.name)


# ── 4. Generate ──────────────────────────────────

REPORT_DEFAULTS = {
    "health_score": 50,
    "tech_stack": [],
    "architecture": {"nodes": [], "edges": [], "mermaid_code": ""},
    "connections": [],
    "data_flow": [],
    "simple_explanation": "",
    "advanced_explanation": "",
    "vulnerabilities": [],
    "broken_links": [],
    "improvements": [],
    "platform_detected": None,
    "verdict_headline": "",
    "verdict_subhead": "",
    "verdict_status": "ship_with_caution",
}


def build_prompt(context: str) -> str:
    return f"""You are a security CTO writing an audit for a NON-TECHNICAL founder who built this app with AI tools (Lovable, Bolt, Replit, Cursor, Windsurf, v0). Find the things that would embarrass them in public and explain them in plain English a non-engineer can act on.

Return ONE JSON object with EXACTLY these keys:

1. "health_score" (int 0-100, 0 = unshippable, 100 = ready)
2. "tech_stack" (array of {{"name", "category", "files_using" array, "purpose" one sentence}})
3. "architecture" ({{"nodes": [{{"id","label"}}], "edges": [{{"source","target"}}], "mermaid_code": valid graph LR string}})
4. "connections" (array of {{"from","to","method","description"}})
5. "data_flow" (array of {{"title","steps":[{{"step","action","component","description"}}]}})
6. "simple_explanation" (3-4 plain-English sentences, no jargon)
7. "advanced_explanation" (2-3 technical paragraphs with specific library + pattern references)
8. "vulnerabilities" (array of {{"title","file","line" int or null,"description","severity" one of critical|high|medium|low,"fix_suggestion"}})
9. "broken_links" (array of {{"file","import_path","issue","suggestion"}})
10. "improvements" (array of {{"title","category","priority" high|medium|low,"description","effort"}})
11. "platform_detected" (string naming the AI builder e.g. "Lovable" if signatures are present, else null)
12. "verdict_headline" (ONE declarative sentence the founder reads first. If criticals exist, lead with the count and the most serious example, e.g. "2 critical issues. Your /admin endpoint has no login check." If clean: "No serious issues found.")
13. "verdict_subhead" (one short follow-on sentence grounded in the code, e.g. "The admin router in api/admin.py never checks the session.")
14. "verdict_status" (one of "do_not_ship" | "ship_with_caution" | "ready_to_ship")

Hard rules:
- Each context chunk starts with "### <file path> (lines a-b)". Only cite files and lines that appear in those headers — never invent them. Use null for "line" if unsure.
- Only report issues you can see evidence of in the context. Do not claim anything was exploited or tested live.
- Write the consequence, not the pattern: "Anyone can read your customers' emails" beats "Hardcoded credentials in config.py".

Tone: calm, declarative, active voice.

Codebase context:
{context}"""


def generate_analysis_report(repo_path: str) -> dict:
    """Run the full RAG pipeline on a cloned repo. Raises AnalysisError on failure."""
    from app.services.llm_router import active_provider, llm_json

    if not GEMINI_API_KEY:
        raise AnalysisError("The server has no GEMINI_API_KEY configured, so AI analysis can't run.")
    if not Path(repo_path).exists():
        raise AnalysisError("The repository could not be read after cloning.")

    files = load_code_files(repo_path)
    if not files:
        raise AnalysisError("No source code files were found in this repository.")

    chunks = [c for path, text in files for c in chunk_file(path, text)][:MAX_CHUNKS]
    print(f"RAG: {len(files)} files -> {len(chunks)} chunks")

    try:
        context = retrieve_context(chunks)
    except Exception as e:
        raise AnalysisError(f"Embedding/retrieval failed: {str(e)[:200]}")

    print(f"RAG: routing deep scan through provider={active_provider()}")
    result = llm_json(build_prompt(context), pass_type="deep", max_tokens=8192)
    if not isinstance(result, dict):
        raise AnalysisError("The AI service is busy or rate-limited right now. Please try again in a minute.")

    for key, default in REPORT_DEFAULTS.items():
        result.setdefault(key, default)
    result["files_analyzed"] = len(files)
    result["chunks_indexed"] = len(chunks)
    return result
