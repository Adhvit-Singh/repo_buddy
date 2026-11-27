import pytest

from app.services import rag_service
from app.services.rag_service import AnalysisError, chunk_file, generate_analysis_report, load_code_files


def test_chunks_cover_whole_file_with_overlap():
    text = "".join(f"line {i}\n" for i in range(400))  # ~3.2k chars
    chunks = chunk_file("app.py", text, size=1000, overlap=200)

    assert len(chunks) >= 4
    assert chunks[0].text.startswith("line 0\n")
    assert chunks[-1].text.endswith("line 399\n")
    # neighbouring chunks share text (the overlap)
    for a, b in zip(chunks, chunks[1:]):
        assert b.text[:40] in a.text
    # every chunk is cut at a line boundary
    assert all(c.text.endswith("\n") for c in chunks)


def test_chunk_line_numbers_match_content():
    text = "".join(f"row {i}\n" for i in range(1, 301))
    for c in chunk_file("x.py", text, size=500, overlap=100):
        lines = c.text.splitlines()
        assert lines[0] == f"row {c.start_line}"
        assert lines[-1] == f"row {c.end_line}"


def test_labelled_chunk_names_file_and_lines():
    [c] = chunk_file("src/auth.py", "a\nb\n")
    assert c.labelled().startswith("### src/auth.py (lines 1-2)")


def test_chunk_rejects_overlap_not_smaller_than_size():
    with pytest.raises(ValueError):
        chunk_file("a.py", "x" * 50, size=10, overlap=10)


def test_empty_file_gives_no_chunks():
    assert chunk_file("a.py", "   \n\n") == []


def test_load_code_files_skips_vendor_lockfiles_and_huge_files(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')\n")
    (tmp_path / "README.md").write_text("# readme\n")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    (tmp_path / "package-lock.json").write_text("{}")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("x")
    (tmp_path / "big.js").write_text("x" * (rag_service.MAX_FILE_BYTES + 1))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("export {}\n")

    paths = [p for p, _ in load_code_files(str(tmp_path))]
    assert paths == ["README.md", "main.py", "src/app.ts"]


def test_scan_fails_loudly_without_api_key(tmp_path):
    # The old code silently returned a canned "demo" report here.
    (tmp_path / "main.py").write_text("print('hi')\n")
    with pytest.raises(AnalysisError, match="GEMINI_API_KEY"):
        generate_analysis_report(str(tmp_path))


def test_scan_fills_defaults_and_counts(monkeypatch, tmp_path):
    (tmp_path / "main.py").write_text("SECRET = 'x'\n")
    monkeypatch.setattr(rag_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(rag_service, "retrieve_context", lambda chunks: "### main.py (lines 1-2)\nSECRET = 'x'")
    monkeypatch.setattr(
        "app.services.llm_router.llm_json",
        lambda prompt, **kw: {"health_score": 40, "vulnerabilities": [{"title": "Hardcoded secret"}]},
    )

    report = generate_analysis_report(str(tmp_path))
    assert report["health_score"] == 40
    assert report["files_analyzed"] == 1
    assert report["chunks_indexed"] == 1
    assert report["tech_stack"] == []              # default filled in
    assert report["verdict_status"] == "ship_with_caution"


def test_scan_reports_busy_llm_as_error(monkeypatch, tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")
    monkeypatch.setattr(rag_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(rag_service, "retrieve_context", lambda chunks: "ctx")
    monkeypatch.setattr("app.services.llm_router.llm_json", lambda prompt, **kw: None)
    with pytest.raises(AnalysisError, match="busy"):
        generate_analysis_report(str(tmp_path))
