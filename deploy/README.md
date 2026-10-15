# 学生管理系统 服务器部署说明

## 一、准备工作

- 一台阿里云 Ubuntu 服务器（已装好 Nginx，root 用户可登录）
- 本地项目目录：`student-system/`

## 二、上传代码到服务器

在**本地**终端执行（把 `47.110.229.114` 换成你的服务器 IP）：

```bash
cd /Users/kalon/WorkBuddy/2026-10-14-20-01-16
scp -r student-system root@47.110.229.114:/opt/student-system-upload
```

> `scp -r` 会连同 `node_modules`、`.mysql-dev` 一起上传，体积较大。
> 推荐先打包去重再传，见下方「精简上传」。

### 精简上传（推荐）

```bash
cd /Users/kalon/WorkBuddy/2026-10-14-20-01-16/student-system
# 打包时排除大文件
tar --exclude='.mysql-dev' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='.env' --exclude='.DS_Store' \
    -czf /tmp/student-system.tar.gz .
scp /tmp/student-system.tar.gz root@47.110.229.114:/opt/
```

登录服务器后解压：

```bash
ssh root@47.110.229.114
mkdir -p /opt/student-system && tar -xzf /opt/student-system.tar.gz -C /opt/student-system
```

## 三、在服务器上运行部署脚本

```bash
cd /opt/student-system/deploy
bash deploy.sh
```

脚本会自动完成：安装依赖 → 初始化 MySQL → 建库建账号 → 安装后端 → 构建前端 → 配置 systemd 服务 → 配置 Nginx。

## 四、导入本地已有数据（可选）

如果想把本地开发时录入的学生数据也搬到服务器：

```bash
# 本地导出（已生成 deploy/student_db.sql，直接上传即可）
scp deploy/student_db.sql root@47.110.229.114:/opt/

# 服务器导入
mysql -ustudent -p'Student@2026' student_db < /opt/student_db.sql
```

## 五、验证

```bash
curl http://127.0.0.1:8000/api/health     # 应返回 {"status":"ok"}
curl http://127.0.0.1/api/stats           # 应返回统计 JSON
```

浏览器访问 `http://47.110.229.114/` 即可看到系统。

## 六、常用运维命令

```bash
systemctl status student-api      # 查看后端状态
journalctl -u student-api -f      # 实时查看后端日志
systemctl restart student-api     # 重启后端
nginx -t && systemctl reload nginx  # 重新加载 Nginx
```

## 七、安全建议

1. 修改部署脚本中的 `DB_PASS` 为强密码（默认 `Student@2026`）
2. 在阿里云安全组中放行 80 端口（HTTP）
3. 如使用域名，将脚本中的 `DOMAIN` 改为域名并配置 SSL（HTTPS）
