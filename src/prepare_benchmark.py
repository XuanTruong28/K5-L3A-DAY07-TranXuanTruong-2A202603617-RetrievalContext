"""Prepare data/questions.json and data/cases.json from Day 6 benchmark.
Ensures evidence string matches chunk exact characters (preserving newlines).
"""
import json
import re
from pathlib import Path


def main():
    day6_benchmark_path = Path("D:/LAB AI/lab06/K5-L3A-DAY06-2A202603617-DataIngestion/data/benchmark.json")
    with open(day6_benchmark_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    day6_questions = data["questions"]

    chunks_path = Path("data/chunks.json")
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    questions_contract = []
    cases_contract = []

    for q in day6_questions:
        gold_source_id = q["gold_source_id"]
        gold_page = q["gold_page"]
        ev = q["evidence_quote"]
        clean_ev_words = ev.split()

        # Find the exact substring in chunk text
        exact_evidence = ev
        found = False
        for c in chunks:
            if c["source_id"] == gold_source_id and c["page"] == gold_page:
                pattern = r"\s+".join(re.escape(w) for w in clean_ev_words)
                m = re.search(pattern, c["text"])
                if m:
                    exact_evidence = m.group(0)
                    found = True
                    break

        if not found:
            print(f"Warning: exact match not found for {q['id']}")

        q_item = {
            "id": q["id"],
            "split": q["split"],
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "gold": [
                {
                    "source_id": gold_source_id,
                    "page": gold_page,
                    "evidence": exact_evidence
                }
            ]
        }
        if q.get("filter"):
            q_item["filter"] = q["filter"]
        questions_contract.append(q_item)

        cases_contract.append({
            "id": q["id"],
            "split": q["split"],
            "question": q["question"],
            "answerable": True,
            "expected_behavior": "search_and_answer"
        })

    # 2. Add 4 unanswerable questions (2 dev + 2 test) to cases_contract
    unanswerable = [
        {
            "id": "q_unans_dev_01",
            "split": "dev",
            "question": "What are the safety guidelines for growing commercial seaweeds in hydroponic chambers on Mars?",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Tài liệu chỉ khảo sát các hoạt động nuôi trồng rong biển tại Trái Đất, hoàn toàn không có dữ liệu về Sao Hỏa."
        },
        {
            "id": "q_unans_dev_02",
            "split": "dev",
            "question": "What are the European Union regulations regarding seaweed aquaculture licensing enacted in the year 2026?",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Tài liệu FAO được xuất bản năm 2003, không chứa các văn bản pháp quy ban hành năm 2026."
        },
        {
            "id": "q_unans_test_01",
            "split": "test",
            "question": "How is CRISPR-Cas9 genome editing specifically applied to improve the carrageenan yield in Kappaphycus alvarezii?",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Tài liệu chỉ thảo luận về chọn lọc tự nhiên và nhân giống sinh dưỡng, không có phương pháp chỉnh sửa gen CRISPR."
        },
        {
            "id": "q_unans_test_02",
            "split": "test",
            "question": "What is the market share of sodium alginate used as an electrolyte binder in lithium-ion batteries for electric vehicles?",
            "answerable": False,
            "expected_behavior": "search_and_abstain",
            "absence_reason": "Tài liệu chỉ bao gồm các ứng dụng truyền thống (dệt nhuộm, thực phẩm, dược phẩm), không có ứng dụng pin xe điện."
        }
    ]

    cases_contract.extend(unanswerable)

    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "questions.json").write_text(json.dumps(questions_contract, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "cases.json").write_text(json.dumps(cases_contract, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Đã tạo data/questions.json ({len(questions_contract)} câu answerable với exact chunk substring)")
    print(f"✅ Đã tạo data/cases.json ({len(cases_contract)} cases: 17 dev, 7 test)")


if __name__ == "__main__":
    main()
