from retriever import SimpleRAGIndex


def test_search_returns_relevant_chunk():
    idx = SimpleRAGIndex(chunk_size=100, overlap=10)
    docs = [
        ("doc1", "RAG pipelines retrieve context before answering."),
        ("doc2", "Completely unrelated sentence about weather."),
    ]
    idx.build(docs)

    out = idx.search("retrieve context", k=1)
    assert len(out) == 1
    assert "retrieve" in out[0].text.lower() or "context" in out[0].text.lower()


def test_empty_query_returns_empty_list():
    idx = SimpleRAGIndex()
    idx.build([("doc", "hello world")])
    assert idx.search("", k=3) == []
