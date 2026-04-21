from typing import List, Dict


class RetrievalEvaluator:
    """Đánh giá chất lượng Retrieval bằng Hit Rate và MRR."""

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """Hit@K: Có ít nhất 1 expected_id nằm trong top_k retrieved_ids không?"""
        if not expected_ids:
            return 1.0  # Adversarial case, không có expected → skip
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """Mean Reciprocal Rank: 1/vị_trí_đầu_tiên tìm thấy expected_id."""
        if not expected_ids:
            return 1.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    def evaluate_single(self, expected_ids: List[str], retrieved_ids: List[str]) -> Dict:
        return {
            "hit_rate": self.calculate_hit_rate(expected_ids, retrieved_ids),
            "mrr": self.calculate_mrr(expected_ids, retrieved_ids),
        }

    async def evaluate_batch(self, results: List[Dict]) -> Dict:
        """Tính toán trung bình Hit Rate và MRR cho toàn bộ batch kết quả benchmark."""
        if not results:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0, "total": 0, "details": []}

        details = []
        total_hit = 0.0
        total_mrr = 0.0

        for r in results:
            expected = r.get("expected_retrieval_ids", [])
            retrieved = r.get("retrieved_ids", [])
            single = self.evaluate_single(expected, retrieved)
            total_hit += single["hit_rate"]
            total_mrr += single["mrr"]
            details.append({
                "question": r.get("question", ""),
                "expected": expected,
                "retrieved": retrieved,
                **single,
            })

        n = len(results)
        return {
            "avg_hit_rate": total_hit / n,
            "avg_mrr": total_mrr / n,
            "total": n,
            "hits": int(total_hit),
            "misses": n - int(total_hit),
            "details": details,
        }
