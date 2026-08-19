#!/bin/bash
set -e

echo "=========================================================="
echo "🚀 Tự động cài đặt Food Buddy Edge trên VM (2 Core, 4GB RAM)"
echo "=========================================================="

# 1. Update system & install prerequisites
echo "[1/5] Cập nhật hệ thống và cài đặt môi trường cơ bản..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg wget python3 python3-pip python3-venv

# 2. Install Docker & Docker Compose if not exists
if ! command -v docker &> /dev/null
then
    echo "[2/5] Đang cài đặt Docker và Docker Compose..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Configure user for docker
    sudo usermod -aG docker $USER
    echo "Lưu ý: Bạn có thể cần đăng xuất và đăng nhập lại để Docker hoạt động không cần sudo."
else
    echo "[2/5] Docker đã được cài đặt, bỏ qua..."
fi

# 3. Download Model if missing
echo "[3/5] Kiểm tra và tải mô hình Qwen 0.5B GGUF..."
mkdir -p agent-reasoner/models
MODEL_FILE="agent-reasoner/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"

if [ ! -f "$MODEL_FILE" ]; then
    echo "Đang tải mô hình ngôn ngữ (Khoảng 491MB)..."
    wget -q --show-progress -O "$MODEL_FILE" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
else
    echo "Mô hình đã tồn tại, không cần tải lại."
fi

# 4. Build and start containers
echo "[4/5] Đang triển khai các AI Agents qua Docker Compose..."
sudo docker compose up -d --build

# 5. Build Semantic Search Index
echo "[5/5] Đang khởi tạo Vector Database (ChromaDB) cho Semantic Search..."
sudo docker compose run --rm retriever python3 scripts/build_index.py

echo "=========================================================="
echo "✅ HOÀN TẤT CÀI ĐẶT!"
echo "Các Agent đã được triển khai:"
echo " - Retriever: Cổng 8883"
echo " - Reasoner: Cổng 8885"
echo " - Synthesizer: Cổng 8887"
echo ""
echo "Để chạy Web UI, hãy sử dụng lệnh sau:"
echo "cd ui && python3 -m http.server 8080"
echo "Sau đó truy cập: http://<IP_CỦA_VM>:8080"
echo "=========================================================="
