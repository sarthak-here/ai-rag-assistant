from __future__ import annotations

from dataclasses import dataclass

from retriever import retrieve_top_k


@dataclass
class EvalCase:
    question: str
    must_contain: str


CASES = [
    EvalCase("what does rag assistant do?", "retrieves"),
    EvalCase("how are answers grounded?", "documents"),
]


def run_eval() -> tuple[int, int]:
    passed = 0
    for case in CASES:
        out = retrieve_top_k(case.question, k=1)
        text = out[0].text.lower() if out else ""
        if case.must_contain in text:
            passed += 1
    return passed, len(CASES)


if __name__ == "__main__":
    passed, total = run_eval()
    print(f"eval: {passed}/{total} passed")
