"""Controller module connecting LLM via OpenProvider Gateway."""
import json
import os
import re
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLMController:
    def __init__(self, model: str | None = None):
        # Mặc định lấy từ .env
        self.model = model or os.getenv("MODEL_NAME", "gemini-3.8-flash")
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "https://openprovider.tuanpq.com/v1"),
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=120.0,
            max_retries=2
        )

    def decide(self, question: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Quyết định bước tiếp theo: search tiếp hay trả lời câu hỏi."""
        # BƯỚC 1: Nếu chưa tìm kiếm lần nào -> Tạo search query
        if not history:
            prompt = (
                f"Question: {question}\n"
                "Output ONLY a concise, keyword-rich search query to retrieve evidence from the seaweed technical guide. "
                "Do not include quotes or conversational text."
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024
            )
            query = response.choices[0].message.content.strip().strip('"').strip("'")
            return {"action": "search", "query": query or question}

        # BƯỚC 2: Đã có context trả về từ Retriever -> Sinh câu trả lời có trích dẫn nguồn
        latest_event = history[-1]
        context = latest_event.get("context", "")
        context_ids = latest_event.get("context_ids", [])

        system_instruction = (
            "You are a strict grounded question-answering assistant for a seaweed technical document.\n"
            "Rules:\n"
            "1. Answer using the information explicitly stated in the provided CONTEXT. When questions mention a Table, Figure, Chart, or Chapter section, synthesize the answer from the table/figure contents or the accompanying descriptive text and data in the context.\n"
            "2. If the context DOES NOT contain sufficient evidence to answer the question, respond with: 'Không đủ bằng chứng để trả lời.' and citations: [].\n"
            "3. If evidence is present, provide a direct, clear and complete factual answer.\n"
            "4. Every factual claim must be followed by its source citation tag in brackets, e.g., [fao_seaweed_guide_p13_b001].\n"
            "5. Return your answer as a JSON object with two fields:\n"
            "   - 'answer': string containing the answer with citation tags [chunk_id]\n"
            "   - 'citations': list of valid cited chunk IDs that are present in AVAILABLE CHUNK IDS\n"
            "Output RAW JSON only without markdown formatting."
        )

        user_content = (
            f"AVAILABLE CHUNK IDS: {context_ids}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            "JSON RESPONSE:"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.0,
            max_tokens=1024
        )

        raw_text = response.choices[0].message.content.strip()
        # Xóa markdown code block nếu model trả về ```json ... ```
        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()

        try:
            data = json.loads(clean_json)
            ans = str(data.get("answer", "")).strip()
            cits = data.get("citations", [])
            if not isinstance(cits, list):
                cits = []

            # Nếu câu trả lời là từ chối hoặc rỗng
            if not ans or "Không đủ bằng chứng để trả lời" in ans:
                return {
                    "action": "answer",
                    "answer": "Không đủ bằng chứng để trả lời.",
                    "citations": []
                }

            # 1. Trích xuất tất cả chunk_id thực sự xuất hiện dạng [chunk_id] trong answer
            text_cits = [cid for cid in context_ids if f"[{cid}]" in ans]

            # 2. Kiểm tra các citation trong list của model
            model_cits = [cid for cid in cits if cid in context_ids]

            # 3. Đồng bộ: Nếu model có cited chunk nhưng chưa ghi [chunk] trong text, gắn thêm vào cuối
            final_cits = list(text_cits)
            for cid in model_cits:
                if cid not in final_cits:
                    ans += f" [{cid}]"
                    final_cits.append(cid)

            # Nếu vẫn không có citation nào từ context
            if not final_cits:
                return {
                    "action": "answer",
                    "answer": "Không đủ bằng chứng để trả lời.",
                    "citations": []
                }

            return {
                "action": "answer",
                "answer": ans,
                "citations": final_cits
            }
        except Exception:
            # Fallback nếu parse JSON lỗi: trích xuất regex [chunk_id]
            found_cits = [cid for cid in context_ids if f"[{cid}]" in raw_text]
            if found_cits:
                ans_clean = raw_text
                for cid in found_cits:
                    if f"[{cid}]" not in ans_clean:
                        ans_clean += f" [{cid}]"
                return {"action": "answer", "answer": ans_clean, "citations": found_cits}
            return {"action": "answer", "answer": "Không đủ bằng chứng để trả lời.", "citations": []}