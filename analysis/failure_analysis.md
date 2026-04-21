# Báo cáo Phân tích Thất bại (Failure Analysis Report) - Real Data

## 1. Tổng quan Benchmark
- **Tổng số cases:** 56 (50 normal + 6 adversarial)
- **Tỉ lệ Pass/Fail:** 43/13 (Pass Rate: 76.8%)
- **Điểm trung bình (V2):** 3.58 / 5.0
- **Retrieval Metrics:**
    - Hit Rate @3: 98.2%
    - MRR: 90.80%
- **Độ tin cậy Judge:**
    - Agreement Rate: ~90.2%
- **Hiệu năng & Chi phí:**
    - Tổng thời gian (V2): 39.4s
    - Tổng chi phí (V2): $0.0824
    - Tiết kiệm chi phí so với V1: **18.3%**

---

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Tỷ lệ | Nguyên nhân dự kiến |
|----------|----------|--------|---------------------|
| Hallucination | 12 | 21.4% | Model sinh thông tin không có trong context dù Retrieval đúng |
| Retrieval Failure | 1 | 1.8% | Không tìm thấy tài liệu liên quan cho case cực khó |

---

## 3. Phân tích 5 Whys (Các lỗi điển hình)

### Case #1: Hallucination trong câu hỏi "extreme_trick"
1. **Symptom:** Agent trả lời sai về điều kiện kết hợp giữa giảm giá và bảo hành.
2. **Why 1:** LLM bị nhầm lẫn giữa hai chính sách khác nhau trong context.
3. **Why 2:** Câu hỏi được thiết kế để lừa (trick) bằng cách đưa ra các điều kiện chồng chéo.
4. **Why 3:** System Prompt của Agent chưa có chỉ thị mạnh mẽ về việc phân tách các thực thể chính sách.
5. **Why 4:** Agent V2 dù đã cải thiện nhưng vẫn chưa xử lý tốt logic phức tạp đa bước.
6. **Root Cause:** Khả năng suy luận (reasoning) của model mini (gpt-4o-mini) còn giới hạn khi đối mặt với các bẫy logic tinh vi.

### Case #2: Retrieval Failure
1. **Symptom:** Agent trả lời "Tôi không biết" cho một câu hỏi thuộc phạm vi tài liệu.
2. **Why 1:** Không có ID tài liệu nào được trích dẫn (retrieved_ids rỗng).
3. **Why 2:** Keyword matching thất bại do câu hỏi sử dụng thuật ngữ kỹ thuật khác hoàn toàn với tài liệu.
4. **Why 3:** Chúng ta đang sử dụng thuật toán tìm kiếm từ khóa đơn giản thay vì Semantic Search (Embeddings).
5. **Why 4:** Ingestion pipeline chưa thực hiện mở rộng từ điển (synonyms).
6. **Root Cause:** Hệ thống Retrieval thiếu khả năng hiểu ngữ nghĩa (semantic understanding).

---

## 4. Phân tích Regression (V1 vs V2)
| Metric | Agent V1 (Base) | Agent V2 (Optimized) | Delta |
|--------|-----------------|----------------------|-------|
| Avg Score | 3.14 | 3.58 | **+0.437** |
| Hit Rate | 98.2% | 98.2% | +0.00% |
| MRR | 90.80% | 90.80% | +0.00% |
| Cost | $0.1009 | $0.0824 | **-18.3%** |

**Kết luận:** Bản V2 đạt yêu cầu Release Gate do điểm số cải thiện đáng kể (+0.437) và chi phí giảm sâu (-18.3%) nhờ tối ưu hóa Token.

---

## 5. Kế hoạch cải tiến (Action Plan)
- [ ] Triển khai **Semantic Search** (Vector DB/Embeddings) để xóa bỏ 1.8% lỗi Retrieval Failure.
- [ ] Nâng cấp model generation lên **GPT-4o** (Full) cho các case được phân loại là "hard" để giảm Hallucination.
- [ ] Bổ sung bước **Chain-of-Thought** vào System Prompt để cải thiện khả năng suy luận logic.
- [ ] Tối ưu hóa Chunking strategy: Chuyển sang Semantic Chunking để đảm bảo context không bị cắt rời.
