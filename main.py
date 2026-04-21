import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from agent.main_agent import MainAgent

# ─── Pricing Constants ───
OPENAI_COST_PER_1K_INPUT = {"gpt-4o-mini": 0.00015, "gpt-4o": 0.0025}
OPENAI_COST_PER_1K_OUTPUT = {"gpt-4o-mini": 0.0006, "gpt-4o": 0.01}

# ─── Release Gate Thresholds ───
GATE_MIN_SCORE = 3.0
GATE_MAX_SCORE_DROP = -0.5
GATE_MAX_COST_INCREASE_PCT = 20.0


def calculate_summary(results, version, elapsed, judge: LLMJudge) -> dict:
    total = len(results)
    valid = [r for r in results if r.get("status") != "error"]
    n = len(valid) or 1

    pass_count = sum(1 for r in valid if r.get("status") == "pass")
    fail_count = sum(1 for r in valid if r.get("status") == "fail")
    error_count = total - len(valid)

    avg_score = sum(r["judge"]["final_score"] for r in valid) / n
    avg_hit_rate = sum(r["retrieval"]["hit_rate"] for r in valid) / n
    avg_mrr = sum(r["retrieval"]["mrr"] for r in valid) / n
    avg_agreement = sum(r["judge"]["agreement_rate"] for r in valid) / n
    avg_latency = sum(r.get("latency", 0) for r in valid) / n
    total_tokens = sum(r.get("metadata", {}).get("tokens_used", 0) for r in valid)

    cost_report = judge.get_cost_report()

    # Phân bố theo difficulty
    difficulty_breakdown = {}
    for r in valid:
        d = r.get("metadata", {}).get("difficulty", "unknown")
        if d not in difficulty_breakdown:
            difficulty_breakdown[d] = {"count": 0, "avg_score": 0, "total_score": 0}
        difficulty_breakdown[d]["count"] += 1
        difficulty_breakdown[d]["total_score"] += r["judge"]["final_score"]
    for d in difficulty_breakdown:
        c = difficulty_breakdown[d]["count"]
        difficulty_breakdown[d]["avg_score"] = round(difficulty_breakdown[d]["total_score"] / c, 2)
        del difficulty_breakdown[d]["total_score"]

    return {
        "metadata": {
            "version": version,
            "total": total,
            "pass": pass_count,
            "fail": fail_count,
            "errors": error_count,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": round(elapsed, 1),
        },
        "metrics": {
            "avg_score": round(avg_score, 3),
            "hit_rate": round(avg_hit_rate, 3),
            "mrr": round(avg_mrr, 3),
            "agreement_rate": round(avg_agreement, 3),
            "avg_latency_seconds": round(avg_latency, 3),
        },
        "cost": {
            "total_judge_cost_usd": cost_report["total_cost_usd"],
            "total_tokens": cost_report["total_tokens"],
            "total_tokens_input": cost_report["total_tokens_input"],
            "total_tokens_output": cost_report["total_tokens_output"],
            "agent_tokens_used": total_tokens,
            "models_used": cost_report["models_used"],
        },
        "difficulty_breakdown": difficulty_breakdown,
    }


def release_gate_decision(v1_summary, v2_summary) -> dict:
    """Auto-Gate: quyết định Release hoặc Rollback dựa trên metrics."""
    v1m = v1_summary["metrics"]
    v2m = v2_summary["metrics"]

    score_delta = v2m["avg_score"] - v1m["avg_score"]
    hit_rate_delta = v2m["hit_rate"] - v1m["hit_rate"]
    mrr_delta = v2m["mrr"] - v1m["mrr"]

    v1_cost = v1_summary["cost"]["total_judge_cost_usd"]
    v2_cost = v2_summary["cost"]["total_judge_cost_usd"]
    cost_change_pct = ((v2_cost - v1_cost) / v1_cost * 100) if v1_cost > 0 else 0

    checks = {
        "score_improved": score_delta >= GATE_MAX_SCORE_DROP,
        "meets_min_score": v2m["avg_score"] >= GATE_MIN_SCORE,
        "hit_rate_stable": hit_rate_delta >= -0.1,
        "cost_acceptable": cost_change_pct <= GATE_MAX_COST_INCREASE_PCT,
    }

    all_passed = all(checks.values())

    return {
        "decision": "APPROVE_RELEASE" if all_passed else "BLOCK_RELEASE",
        "checks": checks,
        "deltas": {
            "score": round(score_delta, 3),
            "hit_rate": round(hit_rate_delta, 3),
            "mrr": round(mrr_delta, 3),
            "cost_change_pct": round(cost_change_pct, 1),
        },
        "v1_metrics": v1m,
        "v2_metrics": v2m,
    }


async def run_benchmark(agent_version: str, version_label: str) -> tuple:
    print(f"\n🚀 Khởi động Benchmark cho {version_label}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng.")
        return None, None, None

    print(f"  📋 Loaded {len(dataset)} test cases")

    agent = MainAgent(version=agent_version)
    judge = LLMJudge(judge_models=["gpt-4o", "gpt-4o-mini"])
    runner = BenchmarkRunner(agent, judge, batch_size=5)

    start = time.perf_counter()
    results = await runner.run_all(dataset)
    elapsed = time.perf_counter() - start

    summary = calculate_summary(results, version_label, elapsed, judge)

    print(f"  ⏱️ Hoàn tất trong {elapsed:.1f}s")
    print(f"  📊 Score: {summary['metrics']['avg_score']:.2f} | Hit Rate: {summary['metrics']['hit_rate']:.1%} | MRR: {summary['metrics']['mrr']:.2%}")
    print(f"  💰 Cost: ${summary['cost']['total_judge_cost_usd']:.4f} ({summary['cost']['total_tokens']} tokens)")

    return results, summary, judge


async def main():
    print("=" * 60)
    print("🏭 AI EVALUATION FACTORY - Lab Day 14")
    print("=" * 60)

    # ─── V1 Benchmark ───
    v1_results, v1_summary, v1_judge = await run_benchmark("v1", "Agent_V1_Base")
    if not v1_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    # ─── V2 Benchmark ───
    v2_results, v2_summary, v2_judge = await run_benchmark("v2", "Agent_V2_Optimized")
    if not v2_summary:
        return

    # ─── Regression Analysis ───
    print("\n" + "=" * 60)
    print("📊 REGRESSION ANALYSIS: V1 vs V2")
    print("=" * 60)

    gate = release_gate_decision(v1_summary, v2_summary)

    print(f"\n  Score:    V1={v1_summary['metrics']['avg_score']:.2f} → V2={v2_summary['metrics']['avg_score']:.2f} (Δ={gate['deltas']['score']:+.3f})")
    print(f"  Hit Rate: V1={v1_summary['metrics']['hit_rate']:.1%} → V2={v2_summary['metrics']['hit_rate']:.1%} (Δ={gate['deltas']['hit_rate']:+.3f})")
    print(f"  MRR:      V1={v1_summary['metrics']['mrr']:.2%} → V2={v2_summary['metrics']['mrr']:.2%} (Δ={gate['deltas']['mrr']:+.3f})")
    print(f"  Cost:     Δ={gate['deltas']['cost_change_pct']:+.1f}%")

    print(f"\n  Gate Checks:")
    for check, passed in gate["checks"].items():
        icon = "✅" if passed else "❌"
        print(f"    {icon} {check}")

    if gate["decision"] == "APPROVE_RELEASE":
        print("\n  🟢 QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE RELEASE)")
    else:
        print("\n  🔴 QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")

    # ─── Failure Clustering ───
    print("\n" + "=" * 60)
    print("🔍 FAILURE CLUSTERING")
    print("=" * 60)

    failed_cases = [r for r in v2_results if r.get("status") == "fail"]
    retrieval_failures = [r for r in v2_results if r.get("retrieval", {}).get("hit_rate", 1) == 0]

    print(f"  Total Failed: {len(failed_cases)}/{len(v2_results)}")
    print(f"  Retrieval Misses: {len(retrieval_failures)}")

    clusters = {}
    for r in failed_cases:
        score = r["judge"]["final_score"]
        hit = r["retrieval"]["hit_rate"]
        if hit == 0:
            cluster = "retrieval_failure"
        elif score <= 2:
            cluster = "hallucination"
        else:
            cluster = "partial_answer"
        clusters.setdefault(cluster, []).append(r)

    for cluster_name, cases in clusters.items():
        print(f"  📁 {cluster_name}: {len(cases)} cases")

    # ─── Save Reports ───
    os.makedirs("reports", exist_ok=True)

    # summary.json với regression data
    final_summary = {
        **v2_summary,
        "regression": gate,
        "v1_summary": v1_summary,
    }
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(final_summary, f, ensure_ascii=False, indent=2)

    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Reports saved:")
    print(f"  → reports/summary.json")
    print(f"  → reports/benchmark_results.json")
    print(f"\n🏁 Benchmark hoàn tất!")


if __name__ == "__main__":
    asyncio.run(main())
