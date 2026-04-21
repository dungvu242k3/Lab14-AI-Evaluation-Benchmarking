import asyncio
import os
import json
from typing import Dict, Any, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JUDGE_RUBRIC = """Bạn là giám khảo AI chuyên nghiệp. Đánh giá câu trả lời của AI Agent dựa trên các tiêu chí:

1. **Accuracy (Chính xác):** Câu trả lời có đúng so với Ground Truth không?
2. **Completeness (Đầy đủ):** Câu trả lời có bao phủ hết các điểm chính không?
3. **Relevance (Liên quan):** Câu trả lời có trả lời đúng câu hỏi được đặt ra không?
4. **Professionalism (Chuyên nghiệp):** Giọng văn có phù hợp với vai trò hỗ trợ khách hàng không?

Chấm điểm tổng hợp từ 1-5:
- 1: Hoàn toàn sai hoặc không liên quan
- 2: Có một ít thông tin đúng nhưng nhiều sai sót
- 3: Đúng một phần, thiếu chi tiết quan trọng
- 4: Tốt, đúng hầu hết nhưng thiếu 1-2 chi tiết
- 5: Xuất sắc, chính xác và đầy đủ

Trả về JSON:
{{"score": <1-5>, "reasoning": "<giải thích ngắn gọn lý do chấm điểm>"}}"""


class LLMJudge:
    """Multi-Judge Consensus Engine: sử dụng 2 model OpenAI khác nhau để đánh giá."""

    COST_PER_1K_INPUT = {"gpt-4o": 0.0025, "gpt-4o-mini": 0.00015}
    COST_PER_1K_OUTPUT = {"gpt-4o": 0.01, "gpt-4o-mini": 0.0006}

    def __init__(self, judge_models: List[str] = None):
        self.judge_models = judge_models or ["gpt-4o", "gpt-4o-mini"]
        self.total_cost = 0.0
        self.total_tokens_input = 0
        self.total_tokens_output = 0

    async def _call_judge(self, model: str, question: str, answer: str, ground_truth: str) -> Dict:
        user_prompt = (
            f"Câu hỏi: {question}\n\n"
            f"Câu trả lời của Agent: {answer}\n\n"
            f"Ground Truth (Đáp án chuẩn): {ground_truth}\n\n"
            f"Hãy chấm điểm."
        )

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": JUDGE_RUBRIC},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        usage = response.usage
        input_cost = (usage.prompt_tokens / 1000) * self.COST_PER_1K_INPUT.get(model, 0.001)
        output_cost = (usage.completion_tokens / 1000) * self.COST_PER_1K_OUTPUT.get(model, 0.004)
        self.total_cost += input_cost + output_cost
        self.total_tokens_input += usage.prompt_tokens
        self.total_tokens_output += usage.completion_tokens

        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        return {
            "model": model,
            "score": parsed.get("score", 3),
            "reasoning": parsed.get("reasoning", ""),
            "tokens": {"input": usage.prompt_tokens, "output": usage.completion_tokens},
            "cost": round(input_cost + output_cost, 6),
        }

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """Gọi song song 2 model Judge, tính Agreement Rate và xử lý xung đột."""
        tasks = [self._call_judge(m, question, answer, ground_truth) for m in self.judge_models]
        judge_results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = [r for r in judge_results if isinstance(r, dict)]
        error_results = [str(r) for r in judge_results if isinstance(r, Exception)]

        if not valid_results:
            return {
                "final_score": 0,
                "agreement_rate": 0,
                "individual_scores": {},
                "reasoning": "All judges failed",
                "errors": error_results,
            }

        scores = {r["model"]: r["score"] for r in valid_results}
        all_scores = list(scores.values())
        score_spread = max(all_scores) - min(all_scores)

        # Tính Agreement Rate: 1.0 nếu đồng ý hoàn toàn, giảm dần theo sai lệch
        agreement = max(0.0, 1.0 - (score_spread / 4.0))

        # Xử lý xung đột: nếu lệch > 1.5 điểm → dùng điểm trung vị thay vì trung bình
        if score_spread > 1.5 and len(all_scores) >= 2:
            final_score = sorted(all_scores)[len(all_scores) // 2]  # Median
            conflict_resolution = "median_due_to_high_spread"
        else:
            final_score = sum(all_scores) / len(all_scores)
            conflict_resolution = "average"

        reasonings = {r["model"]: r["reasoning"] for r in valid_results}
        total_case_cost = sum(r["cost"] for r in valid_results)

        return {
            "final_score": round(final_score, 2),
            "agreement_rate": round(agreement, 2),
            "individual_scores": scores,
            "reasoning": reasonings,
            "conflict_resolution": conflict_resolution,
            "score_spread": score_spread,
            "cost": round(total_case_cost, 6),
        }

    async def check_position_bias(self, question: str, answer_a: str, answer_b: str) -> Dict:
        """Kiểm tra Position Bias bằng cách đổi thứ tự 2 câu trả lời."""
        prompt_ab = (
            f"Câu hỏi: {question}\n"
            f"Câu trả lời A: {answer_a}\n"
            f"Câu trả lời B: {answer_b}\n"
            f"Hãy chọn câu trả lời tốt hơn (A hoặc B) và giải thích."
        )
        prompt_ba = (
            f"Câu hỏi: {question}\n"
            f"Câu trả lời A: {answer_b}\n"
            f"Câu trả lời B: {answer_a}\n"
            f"Hãy chọn câu trả lời tốt hơn (A hoặc B) và giải thích."
        )

        model = self.judge_models[0]
        resp_ab, resp_ba = await asyncio.gather(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_ab}],
                temperature=0.1,
            ),
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_ba}],
                temperature=0.1,
            ),
        )

        choice_ab = resp_ab.choices[0].message.content
        choice_ba = resp_ba.choices[0].message.content

        return {
            "original_order_preference": choice_ab[:200],
            "swapped_order_preference": choice_ba[:200],
            "has_position_bias": "A" in choice_ab[:10] and "A" in choice_ba[:10],
        }

    def get_cost_report(self) -> Dict:
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_tokens": self.total_tokens_input + self.total_tokens_output,
            "models_used": self.judge_models,
        }
