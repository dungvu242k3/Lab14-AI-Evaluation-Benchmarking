# Báo cáo cá nhân 
**Họ tên:** Phạm Minh Trí

**Mã học viên:** 2A202600264

**Nhóm:** C1-C401


## 1. Đóng góp kỹ thuật (Engineering Contribution)

### Modules phụ trách:
- **`engine/llm_judge.py`**: Kiến trúc hệ thống Multi-Judge Consensus Engine. Triển khai việc gọi song song nhiều mô hình (GPT-4o, Claude 3.5 Sonnet) để chấm điểm câu trả lời của Agent.
- **Agreement Logic**: Xây dựng logic tính toán độ đồng thuận và tự động xử lý xung đột điểm số khi các Judge không thống nhất.

### Git Commits tiêu biểu:
- `feat: multi-judge consensus with GPT and Claude integration`
- `feat: implement agreement rate and score calibration logic`

---

## 2. Kiến thức chuyên sâu (Technical Depth)

### Cohen's Kappa & Agreement Rate:
Trong một hệ thống đánh giá bằng AI, độ tin cậy của một Judge đơn lẻ là không đủ. Mình sử dụng **Agreement Rate** để đo mức độ "đồng ý" giữa các chuyên gia AI.
- Công thức: `Agreement = 1.0 - (Score_Spread / Max_Potential_Spread)`.
- **Calibration (Hiệu chuẩn):** Nếu điểm số giữa 2 Judge lệch nhau quá 1.5 điểm (trên thang 5), hệ thống sẽ đánh dấu đây là một "Controversial Case" và ưu tiên lấy điểm Trung vị (Median) thay vì Trung bình cộng (Mean) để loại bỏ các điểm số cực đoan.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Chi phí tăng vọt khi dùng nhiều Judge mạnh (Claude + GPT)
- **Mô tả:** Chạy 50 cases với 2 Judge flagship tốn khoảng $1-$2 cho mỗi lần run, làm ngân sách nhóm cạn kiệt nhanh.
- **Giải pháp:** Mình đã đề xuất kỹ thuật **Tiered Judging**. Sử dụng GPT-4o-mini làm Judge mặc định. Nếu điểm của nó thấp hơn ngưỡng 3/5, hệ thống mới gọi thêm Judge "Expert" (GPT-4o) để kiểm chứng lại. Điều này giúp giảm ~60% chi phí nhưng vẫn giữ được độ chính xác cho các cases khó.

### Vấn đề: LLM Judge trả về điểm kèm giải thích dài dòng khó parse
- **Mô tả:** Mặc dù yêu cầu JSON, nhưng LLM hay thêm lời bình "Here is the evaluation..." làm lỗi bước hậu xử lý.
- **Giải pháp:** Sử dụng Regular Expression để bóc tách khối JSON nằm giữa cặp dấu ` ```json ... ``` ` và ép kiểu nghiêm ngặt bằng Pydantic.
