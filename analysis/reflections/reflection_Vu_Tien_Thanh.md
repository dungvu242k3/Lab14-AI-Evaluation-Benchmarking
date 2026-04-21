# Báo cáo Cá nhân — Vũ Tiến Thành

## 1. Đóng góp kỹ thuật (Engineering Contribution)

### Modules phụ trách:
- **`analysis/failure_analysis.md`**: Phân tích sâu 50+ cases để tìm ra nguyên nhân gốc rễ của các lỗi (Hallucination, Lack of context). Áp dụng phương pháp "5 Whys".
- **`check_lab.py` & Validation logic**: Xây dựng hệ thống tự động kiểm tra định dạng dữ liệu (Sanity Check) và logic **Regression Release Gate** để so sánh V1 vs V2.

### Git Commits tiêu biểu:
- `feat: implement automated regression gate and sanity checker`

---

## 2. Kiến thức chuyên sâu (Technical Depth)

### Position Bias (Thiên kiến vị trí):
LLM làm Judge thường có xu hướng ưu tiên câu trả lời đầu tiên mà nó đọc được (Position 1 Bias). 
- **Cách phát hiện:** Mình triển khai logic đổi chỗ câu trả lời A và B rồi cho Judge chấm lại. Nếu Judge đổi lựa chọn từ A sang B -> Judge khách quan. Nếu Judge vẫn chọn vị trí 1 bất kể nội dung -> Hệ thống bị Position Bias.
- **Giải pháp:** Trong module của mình, nếu phát hiện Bias, hệ thống sẽ yêu cầu Judge thứ 3 làm người phân xử (Tie-breaker).

### Phân tích nguyên nhân gốc rễ (Root Cause Analysis):
Thay vì chỉ nói "Agent trả lời sai", mình phân tách lỗi thành các tầng:
1. Retrieval Failure (Không tìm đúng document).
2. Context Overflow (Tìm đúng nhưng context quá dài làm nhiễu LLM).
3. Generation Failure (Tìm đúng, context chuẩn nhưng LLM suy luận sai).

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Dashboard báo Agent V2 tệ hơn V1 dù đã cải thiện Prompt
- **Mô tả:** Sau khi sửa Prompt, điểm số tổng quát lại giảm mạnh làm cả nhóm bối rối.
- **Giải pháp:** Sử dụng công cụ `check_lab.py` để phân tích delta. Mình phát hiện ra LLM Judge mới (gpt-4o) khó tính hơn Judge cũ. Sau khi bình chuẩn hóa (normalization) lại thang điểm, em chứng minh được V2 thực chất tốt hơn ở các câu hỏi khó, giúp nhóm tự tin báo cáo.

### Vấn đề: JSON Schema thay đổi liên tục gây lỗi script check
- **Mô tả:** Các bạn trong nhóm thay đổi format output mà không báo, làm module check của em bị crash.
- **Giải pháp:** Em đã xây dựng một file `schema_definition.py` dùng chung cho toàn bộ dự án. Bất kỳ thay đổi nào cũng phải cập nhật vào Schema này trước, giúp code của cả nhóm luôn đồng bộ và script check luôn hoạt động.
