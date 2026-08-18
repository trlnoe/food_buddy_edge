# Food Buddy Edge 🍔🧠

Food Buddy Edge là một hệ thống AI tư vấn ẩm thực địa phương (Local Food AI Advisor) chạy hoàn toàn trên thiết bị Edge / VM cấu hình thấp. Hệ thống được thiết kế theo kiến trúc Micro-Agents, giúp dễ dàng mở rộng và tối ưu hóa tài nguyên phần cứng.

Dự án này được tối ưu đặc biệt để có thể triển khai trơn tru trên **Máy ảo (VM) cấu hình chỉ với 2 Core CPU & 4GB RAM**, không yêu cầu GPU rời, bằng cách sử dụng GGUF model với Llama.cpp.

---

## 🏗 Kiến Trúc Hệ Thống (Micro-Agents)

Hệ thống bao gồm 4 thành phần chính:

1. **Agent Retriever (Port 8883):**
   - Nhiệm vụ: Tìm kiếm và trích xuất dữ liệu nhà hàng từ Cơ sở dữ liệu Vector (ChromaDB).
   - Tech-stack: FastAPI, ChromaDB, Sentence-Transformers (tối ưu hóa chạy trên CPU).

2. **Agent Reasoner (Port 8885):**
   - Nhiệm vụ: Xử lý ngôn ngữ tự nhiên, phân tích ngữ cảnh, suy luận và đưa ra khuyến nghị nhà hàng phù hợp nhất.
   - Tech-stack: FastAPI, Llama.cpp (Qwen 2.5 0.5B Instruct GGUF Q4_K_M).
   - Tối ưu: Được cấu hình để giới hạn số luồng (2 threads) phù hợp với VM 2 Core, ngăn ngừa hiện tượng quá tải (OOM).

3. **Agent Synthesizer (Port 8887):**
   - Nhiệm vụ: Orchestrator chính, nhận request từ người dùng, điều phối Retriever và Reasoner, tổng hợp kết quả và trả về cho Frontend.
   - Tech-stack: FastAPI, Async httpx.

4. **Web UI (Port 8080):**
   - Giao diện người dùng dạng tĩnh (HTML/CSS/JS) giao tiếp trực tiếp với Agent Synthesizer.

---

## 🚀 Yêu Cầu Hệ Thống (System Requirements)

- **Hệ điều hành:** Ubuntu 20.04 / 22.04 LTS (Khuyên dùng)
- **CPU:** Tối thiểu 2 Cores
- **RAM:** Tối thiểu 4GB
- **Ổ cứng:** Trống tối thiểu 2GB cho dự án (để lưu trữ Docker Images và AI Models)
- **Software:** Docker, Docker Compose, Python 3.

---

## 🛠 Hướng Dẫn Triển Khai Nhanh (Auto Install Script)

Cách dễ nhất để đảm bảo mã nguồn tái lập hoàn hảo trên một máy VM mới tinh là sử dụng Script tự động cài đặt. Script này sẽ:
1. Cài đặt Docker & Docker Compose (nếu chưa có).
2. Tự động tải mô hình AI `Qwen2.5-0.5B` về đúng thư mục.
3. Build và khởi chạy tất cả các Agents thông qua Docker Compose.

**Bước 1: Chạy Script Cài Đặt**
```bash
# Cấp quyền thực thi cho file script
chmod +x install.sh

# Chạy script
./install.sh
```

*(Đợi khoảng 2-5 phút để Docker tải image và khởi động các Agent)*

**Bước 2: Kiểm Tra Trạng Thái**
Bạn có thể dùng lệnh sau để xem các agent đã chạy lên thành công chưa:
```bash
docker compose ps
```
Nếu thành công, bạn sẽ thấy 3 container `retriever`, `reasoner`, `synthesizer` ở trạng thái **Up**.

**Bước 3: Khởi chạy Giao Diện Web (UI)**
Chạy máy chủ web tĩnh ở chế độ nền (hoặc chạy trong phiên Screen/Tmux):
```bash
cd ui
python3 -m http.server 8080
```
Truy cập giao diện tại: `http://<IP_CỦA_VM>:8080`.

> **⚠️ LƯU Ý QUAN TRỌNG VỀ PORT (ĐỐI VỚI CLOUD VM / VS CODE):**
> Giao diện (Port 8080) cần gọi API ngầm (Port 8887) ở phía backend. 
> - Nếu bạn đang chạy trên Cloud VM hoặc VS Code Server, **bạn bắt buộc phải mở/forward cả Port `8080` VÀ Port `8887`** ra ngoài Internet.
> - Nếu gặp lỗi kết nối API, bạn có thể thay đổi cấu hình kết nối trực tiếp trên trình duyệt bằng cách mở F12 -> Console -> Chạy: `setApiUrl('http://<IP_MỚI>:8887')`.

---

## 📦 Hướng Dẫn Triển Khai Thủ Công (Manual Deployment)

Nếu bạn không muốn dùng script, dưới đây là các bước tái lập hệ thống hoàn toàn thủ công.

### 1. Chuẩn Bị Mô Hình AI
Do máy VM chỉ có 2 Core/4GB RAM, hệ thống bắt buộc sử dụng mô hình GGUF siêu nhẹ (Dưới 500MB).
Tải mô hình vào thư mục của Reasoner:
```bash
mkdir -p agent-reasoner/models
wget -O agent-reasoner/models/qwen2.5-0.5b-instruct-q4_k_m.gguf "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
```

### 2. Cấu Hình Tài Nguyên (Đã được cấu hình sẵn trong docker-compose.yml)
File `docker-compose.yml` của dự án đã được thiết kế chuẩn mực để giới hạn tài nguyên, nhằm tránh sập VM 4GB RAM:
```yaml
# Trích đoạn cấu hình Agent Reasoner
    environment:
      OMP_NUM_THREADS: "2"
      OPENBLAS_NUM_THREADS: "2"
      LLM_THREADS: "2"
    cpuset: "0,1"
    deploy:
      resources:
        limits: { memory: 4G }
```

### 3. Build & Run
Chạy toàn bộ cụm Micro-Agents với Docker Compose:
```bash
docker compose up -d --build
```

### 4. Khởi chạy Web UI
```bash
cd ui && python3 -m http.server 8080
```

---

## 🔍 Gỡ Lỗi (Troubleshooting)

1. **Lỗi "Cannot reach the AI Synthesizer orchestrator"**
   - Nguyên nhân: Trình duyệt không thể với tới Port 8887. 
   - Khắc phục: Kiểm tra tường lửa (Firewall) của VM xem port 8887 đã được mở chưa. Nếu dùng VS Code Remote, mở tab Ports và Add Port 8887.

2. **Lỗi hết RAM (Out of Memory) trên VM**
   - Đảm bảo trong thư mục `agent-reasoner/models/` bạn đang dùng đúng phiên bản GGUF `qwen2.5-0.5b-instruct-q4_k_m.gguf` (Dung lượng khoảng 491MB). 
   - Không được dùng phiên bản 1.5B trở lên nếu máy ảo chỉ có 4GB RAM (Bởi vì hệ điều hành & Vector DB đã chiếm mất một phần RAM đáng kể).

3. **Kiểm tra logs của các Agent**
   - Để xem Reasoner đang tư duy thế nào: `docker compose logs -f reasoner`
   - Để xem hiệu năng Orchestrator: `docker compose logs -f synthesizer`