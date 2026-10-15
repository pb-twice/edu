#!/usr/bin/env bash
# ============================================================
# 学生管理系统 一键部署脚本（阿里云 Ubuntu + root）
# 用法：bash deploy.sh
# 说明：首次运行会安装并配置所有环境；之后重复运行即可更新代码
# ============================================================
set -euo pipefail

APP_DIR=/opt/student-system
APP_USER=student
DB_PASS="Student@2026"
DOMAIN="47.110.229.114"          # 改成你的域名（如有）

echo "==> [1/8] 更新系统并安装基础依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y -q
apt-get install -y -q git python3 python3-venv python3-pip nginx curl \
  mysql-server libmysqlclient-dev pkg-config >/dev/null

echo "==> [2/8] 启动并初始化 MySQL"
systemctl enable --now mysql || service mysql start || true
sleep 2
# 若 root 已可用则跳过；否则用 auth_socket 免密设置密码
if ! mysql -uroot -e "SELECT 1" >/dev/null 2>&1; then
  mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_PASS}'; FLUSH PRIVILEGES;" 2>/dev/null || true
fi
# 创建数据库与专用账号（幂等）
SQL_FILE=$(mktemp)
cat > "$SQL_FILE" <<SQL
CREATE DATABASE IF NOT EXISTS student_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'student'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON student_db.* TO 'student'@'localhost';
FLUSH PRIVILEGES;
SQL
mysql -uroot -p"${DB_PASS}" < "$SQL_FILE" 2>/dev/null || mysql -uroot < "$SQL_FILE"
rm -f "$SQL_FILE"

echo "==> [3/8] 创建应用目录与专用用户"
id -u ${APP_USER} >/dev/null 2>&1 || useradd -r -m -s /bin/bash ${APP_USER}
mkdir -p ${APP_DIR}
chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

echo "==> [4/8] 部署代码"
# 若当前脚本目录即源码，则复制；否则从 git 拉取（可选）
SRC="$(cd "$(dirname "$0")" && pwd)"
if [ -f "${SRC}/backend/requirements.txt" ]; then
  rsync -a --delete --exclude '.mysql-dev' --exclude 'node_modules' --exclude '__pycache__' \
    "${SRC}/" "${APP_DIR}/"
else
  echo "未找到源码，请将脚本放在项目根目录下运行"; exit 1
fi

echo "==> [5/8] 安装后端依赖"
cd ${APP_DIR}/backend
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q

echo "==> [6/8] 写入后端环境配置"
cat > ${APP_DIR}/backend/.env <<ENV
DATABASE_URL=mysql+pymysql://student:${DB_PASS}@127.0.0.1:3306/student_db?charset=utf8mb4
CORS_ORIGINS=*
ENV

echo "==> [7/8] 构建前端并安装 systemd 服务"
# 安装前端依赖并构建
if command -v node >/dev/null 2>&1; then
  cd ${APP_DIR}/frontend
  npm install --silent && npm run build
fi

# 生成 systemd 服务
cat > /etc/systemd/system/student-api.service <<SVC
[Unit]
Description=Student System API (FastAPI)
After=network.target mysql.service

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}/backend
EnvironmentFile=${APP_DIR}/backend/.env
ExecStart=${APP_DIR}/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SVC
systemctl daemon-reload
systemctl enable --now student-api

echo "==> [8/8] 配置 Nginx"
cat > /etc/nginx/sites-available/student <<NGX
server {
    listen 80;
    server_name ${DOMAIN} _;

    # 前端静态文件（若已构建）
    root ${APP_DIR}/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
NGX
ln -sf /etc/nginx/sites-available/student /etc/nginx/sites-enabled/student
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "======================================================"
echo " 部署完成！"
echo " 后端 API:   http://${DOMAIN}/api/health"
echo " 前端页面:   http://${DOMAIN}/"
echo " 数据库:     student_db（账号 student / ${DB_PASS}）"
echo " 服务管理:   systemctl status student-api"
echo "======================================================"
