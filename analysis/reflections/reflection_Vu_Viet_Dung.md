# Báo cáo Cá nhân — Vũ Việt Dũng- 2A202600444

## 1. Đóng góp kỹ thuật (Engineering Contribution)

### Modules phụ trách:
- **`data/synthetic_gen.py`**: Thiết kế và triển khai Synthetic Data Generation (SDG) bằng OpenAI GPT-4o-mini. Tạo 50+ test cases từ 10 tài liệu knowledge base, bao gồm 6 adversarial cases (Red Teaming).
- **`data/HARD_CASES_GUIDE.md`**: Xây dựng bộ quy tắc định nghĩa các câu hỏi "tricky" (Red Teaming) để kiểm tra độ bền của Agent.

### Git Commits tiêu biểu:
- `feat: implement SDG with OpenAI for 50+ golden test cases`
- `docs: create hard cases guide for adversarial testing`

---

## 2. Kiến thức chuyên sâu (Technical Depth)

### Hit Rate (at K):
Hit Rate đo lường tỷ lệ các câu hỏi mà hệ thống Retrieval tìm được document chính xác trong top-K kết quả trả về. 
- Công thức: `Hit Rate = (Số cases tìm đúng ít nhất 1 chunk) / (Tổng số cases)`.
- Ý nghĩa: Đây là metric quan trọng nhất ở giai đoạn "đầu vào". Nếu Hit Rate thấp, chắc chắn câu trả lời của Agent sẽ bị Hallucination hoặc thiếu thông tin vì không "đọc" được đúng tài liệu.

### Tầm quan trọng của Ground Truth Mapping:
Trong SDG, việc map mỗi câu hỏi tự động với `source_id` chuẩn của tài liệu gốc là chìa khóa để tính Hit Rate tự động mà không cần can thiệp thủ công.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Adversarial cases làm giảm Hit Rate giả tạo
- **Mô tả:** Các câu hỏi Red Teaming (ngoài phạm vi knowledge base) khiến Hit Rate giảm xuống vì không có document nào đúng để lấy ra.
- **Giải pháp:** Trong module tính toán, mình đã phân loại các cases này. Nếu `expected_retrieval_ids` rỗng → Case này sẽ được đánh dấu là "Out-of-scope" và không tính vào mẫu số của Hit Rate để bảo vệ độ chính xác của metrics.

### Vấn đề: Rate Limiting khi sinh 50+ cases
- **Mô tả:** Gọi API liên tục để sinh dữ liệu dễ bị lỗi 429.
- **Giải pháp:** Triển khai cơ chế retry với exponential backoff và chia batch nhỏ (10 câu hỏi/lần) để đảm bảo script chạy hoàn tất.
