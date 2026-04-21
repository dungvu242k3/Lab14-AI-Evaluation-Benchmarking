# Báo cáo Cá nhân — Nguyễn Mậu Lân

## 1. Đóng góp kỹ thuật (Engineering Contribution)

### Modules phụ trách:
- **`engine/retrieval_eval.py`**: Triển khai engine đánh giá hiệu năng của Vector Database. Xây dựng logic tính toán các chỉ số chuyên sâu về Search/Retrieval.
- **Tích hợp Metrics**: Đưa các chỉ số đánh giá vào báo cáo tổng quát trong `reports/benchmark_results.json`.

### Git Commits tiêu biểu:
- `feat: implement Hit Rate and MRR metrics for retrieval evaluation`
- `refactor: optimize retrieval evaluator to handle multiple ground truth IDs`

---

## 2. Kiến thức chuyên sâu (Technical Depth)

### MRR (Mean Reciprocal Rank):
MRR đo lường vị trí trung bình của kết quả đúng đầu tiên trong danh sách retrieval. 
- Công thức: `MRR = (1/N) × Σ(1/rank_i)`. 
- So sánh với Hit Rate: Hit Rate chỉ quan tâm "có hay không", còn MRR quan tâm đến "vị trí". Nếu kết quả đúng nằm ở vị trí số 1, `1/rank = 1`. Nếu ở vị trí số 5, `1/rank = 0.2`. MRR cao chứng tỏ hệ thống RAG đang đưa thông tin liên quan nhất lên hàng đầu, giúp LLM đọc ít token hơn nhưng trả lời đúng hơn.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Document đúng nằm ngoài Top-K kết quả
- **Mô tả:** Khi search với K=3, nhưng document chính xác lại nằm ở vị trí số 5. Hit Rate và MRR trả về kết quả thấp làm teamwork lo lắng về chất lượng chunking.
- **Giải pháp:** Mình đã thực hiện experiment với các giá trị K khác nhau (K=3, 5, 10). Kết quả cho thấy tại K=5, MRR tăng đáng kể nhưng độ trễ vẫn chấp nhận được. Mình đã đề xuất nhóm giữ K=5 làm chuẩn cho toàn hệ thống.

### Vấn đề: Xử lý nhiều Ground Truth IDs cho một câu hỏi
- **Mô tả:** Một số câu hỏi phức tạp có thể được trả lời bằng nhiều chunks khác nhau.
- **Giải pháp:** Module của mình cho phép `expected_retrieval_ids` là một danh sách. Chỉ cần 1 trong các chunks này xuất hiện trong Top-K là được tính là 1 "Hit".
