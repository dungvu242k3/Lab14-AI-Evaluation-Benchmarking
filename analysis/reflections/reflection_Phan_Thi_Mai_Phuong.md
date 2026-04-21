# Báo cáo Cá nhân — Phan Thị Mai Phương
**Họ và tên:** Phan Thị Mai Phương

**Mã học viên:** 2A202600281

**Nhóm:** C401-C1

## 1. Đóng góp kỹ thuật (Engineering Contribution)

### Modules phụ trách:
- **`engine/runner.py`**: Tái cấu trúc pipeline từ chạy tuần tự sang chạy bất đồng bộ (Asynchronous) sử dụng thư viện `asyncio`.
- **`main.py`**: Xây dựng hệ thống Integration để kết nối Data Generator, Retrieval Evaluator và LLM Judge thành một chu trình khép kín.
- **Performance Tracking**: Triển khai logic đo lường thời gian thực thi, tính toán Cost & Token usage cho mỗi phiên benchmark.

### Git Commits tiêu biểu:
- `Upload runner.py`(Chứa phần tái cấu trúc pipeline sang xử lý bất đồng bộ bằng asyncio)
- `Upload main.py` (Xây dựng hệ thống tổng hợp và báo cáo chi phí và token usage cho mỗi lần chạy benchmark)

---

## 2. Kiến thức chuyên sâu (Technical Depth)

### Trade-off Chi phí vs Chất lượng:
Trong một Evaluation Factory, chi phí vận hành là yếu tố sống còn. 
- **Chi phí:** Các model mạnh (GPT-4o) có giá cao gấp 10-20 lần model nhỏ (GPT-4o-mini). Nếu chạy 1000 test cases, sự chênh lệch có thể lên tới hàng trăm USD.
- **Giải pháp tối ưu:** Cơ chế tracking token real-time đã được thiết lập. Dựa trên dữ liệu thu thập được, em đề xuất chiến lược: Chỉ dùng model lớn cho "Answer Quality" và dùng model nhỏ cho "Relevance Check" để tối ưu hóa cán cân Chi phí/Chất lượng.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Pipeline chạy quá lâu (50 cases tốn > 10 phút)
- **Mô tả:** Ban đầu mỗi case chạy tuần tự (Request LLM -> Chờ -> Request tiếp), và với 50 cases thì thời gian chờ là rất lớn.
- **Giải pháp:** Chuyển sang dùng `asyncio.gather` để gửi request song song. Tuy nhiên, việc gửi quá nhiều cùng lúc khiến gây ra lỗi Rate Limit (429). Em đã sử dụng `asyncio.Semaphore(value=5)` để giới hạn tối đa 5 requests đồng thời, giúp rút ngắn thời gian xuống còn < 2 phút mà không bị lỗi API.

### Vấn đề: Mất dữ liệu benchmark khi script bị crash giữa chừng
- **Mô tả:** Đang chạy đến case 40 mà lỗi mạng thì mất sạch kết quả của 39 cases trước.
- **Giải pháp:** Em bổ sung logic "Write-on-the-fly". Kết quả của mỗi case sau khi eval xong sẽ được append ngay vào một file tạm hoặc cache. Khi script hoàn tất mới gộp lại thành file `summary.json`.
