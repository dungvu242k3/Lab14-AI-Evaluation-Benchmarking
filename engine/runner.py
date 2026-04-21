import asyncio
import time
from typing import List, Dict
from engine.retrieval_eval import RetrievalEvaluator


class BenchmarkRunner:
    """Async Benchmark Runner: chạy song song với batch control và cost tracking."""

    def __init__(self, agent, judge, batch_size: int = 5):
        self.agent = agent
        self.judge = judge
        self.retrieval_eval = RetrievalEvaluator()
        self.batch_size = batch_size

    async def run_single_test(self, test_case: Dict) -> Dict:
        start = time.perf_counter()

        response = await self.agent.query(test_case["question"])
        agent_latency = time.perf_counter() - start

        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieved_ids = response.get("retrieved_ids", [])
        retrieval_scores = self.retrieval_eval.evaluate_single(expected_ids, retrieved_ids)

        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"],
            response["answer"],
            test_case["expected_answer"],
        )

        total_latency = time.perf_counter() - start
        status = "pass" if judge_result["final_score"] >= 3 else "fail"

        return {
            "test_case": test_case["question"],
            "expected_answer": test_case["expected_answer"],
            "agent_response": response["answer"],
            "retrieved_ids": retrieved_ids,
            "expected_retrieval_ids": expected_ids,
            "latency": round(total_latency, 3),
            "agent_latency": round(agent_latency, 3),
            "retrieval": retrieval_scores,
            "judge": judge_result,
            "status": status,
            "metadata": {
                "difficulty": test_case.get("metadata", {}).get("difficulty", "unknown"),
                "type": test_case.get("metadata", {}).get("type", "unknown"),
                "tokens_used": response.get("metadata", {}).get("tokens_used", 0),
            },
        }

    async def run_all(self, dataset: List[Dict]) -> List[Dict]:
        """Chạy benchmark song song theo batch để tránh rate limit."""
        results = []
        total = len(dataset)

        for i in range(0, total, self.batch_size):
            batch = dataset[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            print(f"  📦 Batch {batch_num}/{total_batches} ({len(batch)} cases)...")

            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, r in enumerate(batch_results):
                if isinstance(r, Exception):
                    print(f"    ⚠️ Case {i+j+1} failed: {r}")
                    results.append({
                        "test_case": batch[j].get("question", "unknown"),
                        "status": "error",
                        "error": str(r),
                        "judge": {"final_score": 0, "agreement_rate": 0},
                        "retrieval": {"hit_rate": 0, "mrr": 0},
                        "metadata": batch[j].get("metadata", {}),
                    })
                else:
                    results.append(r)

        return results
