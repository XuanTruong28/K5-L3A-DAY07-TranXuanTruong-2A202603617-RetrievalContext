"""Evaluation and benchmarking runner for Day 7 Agentic RAG.
Orchestrates Controller, Retrievers, and standard run_agent loop.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Thêm thư mục gốc và thư mục starter vào path để tái sử dụng chuẩn
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "starter"))
sys.path.insert(0, str(ROOT_DIR))

from agentic import run_agent
from baseline import hit as is_evidence_hit
from src.controller import LLMController
from src.retrievers import BM25Retriever, DenseRetriever, HybridRRFRetriever


def load_data(chunks_path: Path, questions_path: Path, split: str):
    """Nạp dữ liệu chunks và câu hỏi theo split (dev hoặc test)."""
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    with open(questions_path, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    questions = [q for q in all_questions if q.get("split") == split]
    return chunks, questions


def evaluate_retrieval_and_context(retriever, questions, budget=1200, top_k=3):
    """Tính các metric ranking (Hit@1, Evidence Hit@3) và Context Evidence Rate."""
    hit1_count = 0
    hit3_count = 0
    context_evidence_count = 0
    answerable_count = 0

    retrieval_logs = []

    for q in questions:
        # Nếu câu hỏi là unanswerable (không có gold) thì không tính vào mẫu số retrieval
        gold = q.get("gold", [])
        if not gold:
            continue

        answerable_count += 1
        flt = q.get("filter")
        hits = retriever.search(q["question"], filters=flt, top_k=top_k)

        # 1. Hit@1: Chunk đầu tiên có chứa evidence không?
        h1 = bool(hits and is_evidence_hit(hits[0], gold))
        if h1:
            hit1_count += 1

        # 2. Evidence Hit@3: Ít nhất 1 trong top-3 chứa evidence không?
        h3 = any(is_evidence_hit(h, gold) for h in hits)
        if h3:
            hit3_count += 1

        # 3. Context Evidence Rate: Sau khi nén theo context budget, context có chứa evidence không?
        # Nén ngữ cảnh: nối text các chunk cho tới khi chạm giới hạn budget
        packed_text = ""
        for h in hits:
            if len(packed_text) + len(h["text"]) <= budget:
                packed_text += "\n" + h["text"]
            else:
                break
        
        has_context_ev = any(g.get("evidence", "") in packed_text for g in gold)
        if has_context_ev:
            context_evidence_count += 1

        retrieval_logs.append({
            "id": q["id"],
            "hit1": h1,
            "hit3": h3,
            "context_hit": has_context_ev,
            "top_ids": [h["id"] for h in hits]
        })

    n = max(answerable_count, 1)
    return {
        "n_answerable": answerable_count,
        "hit1": hit1_count,
        "hit1_rate": round(hit1_count / n * 100, 2),
        "hit3": hit3_count,
        "hit3_rate": round(hit3_count / n * 100, 2),
        "context_rate": round(context_evidence_count / n * 100, 2),
        "logs": retrieval_logs
    }


def main():
    parser = argparse.ArgumentParser(description="Day 7 Agentic RAG Runner")
    parser.add_argument("--split", choices=["dev", "test"], default="dev", help="Tập dữ liệu đánh giá")
    parser.add_argument("--retriever", choices=["dense", "bm25", "hybrid", "all"], default="hybrid", help="Phương pháp retrieval")
    parser.add_argument("--chunks", default="data/chunks.json", help="Đường dẫn file chunks.json")
    parser.add_argument("--questions", default="data/questions.json", help="Đường dẫn file questions.json")
    parser.add_argument("--chroma", default="D:/LAB AI/lab06/K5-L3A-DAY06-2A202603617-DataIngestion/starter/results/chroma", help="Thư mục ChromaDB Day 6")
    parser.add_argument("--output", default="starter/results", help="Thư mục xuất kết quả")
    parser.add_argument("--budget", type=int, default=1200, help="Context budget ký tự")
    parser.add_argument("--top_k", type=int, default=3, help="Top-k chunks truy xuất")
    parser.add_argument("--run_agent", action="store_true", help="Chạy cả vòng lặp Agent với model thật")
    args = parser.parse_args()

    chunks_path = ROOT_DIR / args.chunks
    questions_path = ROOT_DIR / args.questions
    out_dir = ROOT_DIR / args.output
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"🚀 DAY 7 EVALUATION RUNNER · SPLIT: [{args.split.upper()}]")
    print("=" * 70)

    # 1. Nạp dữ liệu
    chunks, questions = load_data(chunks_path, questions_path, args.split)
    print(f" -> Đã nạp {len(chunks)} chunks và {len(questions)} câu hỏi cho split '{args.split}'")

    # 2. Khởi tạo các Retriever
    dense_retriever = DenseRetriever(chroma_path=args.chroma, collection_name="strategy_B")
    bm25_retriever = BM25Retriever(chunks=chunks)
    hybrid_retriever = HybridRRFRetriever(dense_retriever=dense_retriever, bm25_retriever=bm25_retriever)

    retrievers_to_run = {}
    if args.retriever in ("dense", "all"):
        retrievers_to_run["Dense (ChromaDB)"] = dense_retriever
    if args.retriever in ("bm25", "all"):
        retrievers_to_run["BM25 (Lexical)"] = bm25_retriever
    if args.retriever in ("hybrid", "all"):
        retrievers_to_run["Hybrid (Dense + BM25 RRF)"] = hybrid_retriever

    # 3. Đánh giá Retrieval Metrics
    print("\n📊 BẢNG SO SÁNH CHỈ SỐ RETRIEVAL:")
    print("-" * 75)
    print(f"{'Phương pháp':<30} | {'Hit@1':<12} | {'Hit@3':<12} | {'Context Ev. Rate':<15}")
    print("-" * 75)

    comparison_results = {}
    for name, ret in retrievers_to_run.items():
        res = evaluate_retrieval_and_context(ret, questions, budget=args.budget, top_k=args.top_k)
        comparison_results[name] = res
        n = res["n_answerable"]
        print(f"{name:<30} | {res['hit1']}/{n} ({res['hit1_rate']}%) | {res['hit3']}/{n} ({res['hit3_rate']}%) | {res['context_rate']}%")
    print("-" * 75)

    # 4. Nếu có cờ --run_agent: Chạy vòng lặp Agent thật với LLMController
    if args.run_agent:
        print("\n🤖 CHẠY VÒNG LẶP AGENTIC RAG VỚI MODEL THẬT...")
        controller = LLMController()
        # Mặc định dùng Hybrid Retriever làm công cụ tìm kiếm cho Agent
        chosen_retriever = hybrid_retriever if "Hybrid (Dense + BM25 RRF)" in retrievers_to_run else list(retrievers_to_run.values())[0]

        traces = []
        total_time = 0.0
        correct_abstentions = 0
        total_unanswerable = 0
        answered_with_cits = 0
        total_answerable = 0

        for idx, q in enumerate(questions, start=1):
            is_answerable = bool(q.get("gold"))
            if is_answerable:
                total_answerable += 1
            else:
                total_unanswerable += 1

            t0 = time.time()
            flt = q.get("filter")
            
            # Chạy qua vòng lặp chuẩn run_agent của starter
            agent_result = run_agent(
                question=q["question"],
                controller=controller,
                retriever=chosen_retriever,
                filters=flt,
                max_searches=3,
                top_k=args.top_k,
                budget=args.budget
            )
            elapsed = round(time.time() - t0, 2)
            total_time += elapsed

            status = agent_result.get("status")
            ans = agent_result.get("answer", "")
            cits = agent_result.get("citations", [])

            # Đánh giá sơ bộ
            if not is_answerable and status == "abstain":
                correct_abstentions += 1
            if is_answerable and status == "answered" and cits:
                answered_with_cits += 1

            print(f"[{idx}/{len(questions)}] ID: {q['id']} | Status: {status} | Time: {elapsed}s")
            print(f"   Q: {q['question']}")
            print(f"   A: {ans[:120]}... | Cits: {cits}")

            traces.append({
                "query_id": q["id"],
                "split": args.split,
                "question": q["question"],
                "answerable": is_answerable,
                "status": status,
                "answer": ans,
                "citations": cits,
                "events": agent_result.get("events", []),
                "time_sec": elapsed
            })

        # Ghi file traces.json
        trace_file = out_dir / "traces.json"
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(traces, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Đã lưu toàn bộ vết thực thi vào: {trace_file}")

        # In tổng kết
        print("\n📈 TỔNG KẾT AGENT PERFORMANCE:")
        print(f" - Tổng câu hỏi: {len(questions)} ({total_answerable} có đáp án, {total_unanswerable} thiếu bằng chứng)")
        if total_unanswerable > 0:
            print(f" - Abstention chính xác (Từ chối đúng): {correct_abstentions}/{total_unanswerable} ({round(correct_abstentions/total_unanswerable*100, 1)}%)")
        print(f" - Câu có đáp án trả lời kèm Citation: {answered_with_cits}/{total_answerable} ({round(answered_with_cits/max(total_answerable, 1)*100, 1)}%)")
        print(f" - Tổng thời gian chạy: {round(total_time, 2)}s (Trung bình: {round(total_time/len(questions), 2)}s/câu)")
        print(f" - Tổng chi phí: 0 USD (OpenProvider Gateway)")

        # Thống kê theo từng nhóm ADVANCED.md nếu có trường "group"
        groups = {}
        for q, t in zip(questions, traces):
            grp = q.get("group", "general")
            if grp not in groups:
                groups[grp] = {"passed": 0, "total": 0}
            groups[grp]["total"] += 1
            is_passed = (t["answerable"] and t["status"] == "answered" and bool(t["citations"])) or \
                        (not t["answerable"] and t["status"] == "abstain")
            if is_passed:
                groups[grp]["passed"] += 1

        if any(q.get("group") for q in questions):
            print("\n" + "=" * 70)
            print("🏆 BẢNG TỔNG KẾT THỬ THÁCH NÂNG CAO (THEO ADVANCED.MD):")
            print("-" * 70)
            print(f"{'Nhóm test':<24} | {'Đạt / Tổng':<12} | {'Tỷ lệ (%)':<12} | {'Đánh giá':<15}")
            print("-" * 70)
            group_names = {
                "table": "Bảng (Table)",
                "figure": "Ảnh, sơ đồ (Figure)",
                "chart": "Biểu đồ (Chart)",
                "multihop": "Multi-hop",
                "text": "Văn bản (Text)",
                "abstention": "Thiếu bằng chứng"
            }
            total_pass = sum(g["passed"] for g in groups.values())
            for g_key, g_label in group_names.items():
                if g_key in groups:
                    p = groups[g_key]["passed"]
                    tot = groups[g_key]["total"]
                    pct = round(p / tot * 100, 1)
                    eval_str = "Đạt ✅" if pct >= 80 else "Cần chú ý"
                    print(f"{g_label:<24} | {p}/{tot:<10} | {pct}%{'':<6} | {eval_str}")
            print("-" * 70)
            total_pct = round(total_pass / len(questions) * 100, 1)
            final_eval = "ĐẠT THỬ THÁCH BONUS (+15 ĐIỂM) 🎉" if total_pct >= 90.0 else "Chưa đạt ngưỡng 90%"
            print(f"{'TOÀN BỘ TEST':<24} | {total_pass}/{len(questions):<10} | {total_pct}%{'':<6} | {final_eval}")
            print("=" * 70)

    # Lưu kết quả retrieval so sánh
    summary_file = out_dir / f"retrieval_summary_{args.split}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(comparison_results, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu bảng tổng kết Retrieval vào: {summary_file}")


if __name__ == "__main__":
    main()