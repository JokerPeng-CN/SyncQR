# 扫码同步神器（A 扫描 → B 展示/跳转）

## 必读：必须通过 Cloudflare Tunnel 用 HTTPS 打开（否则 HTTP 可能无法唤起相机）

你使用了 `cloudflared` 并通过 `--url http://localhost:7898` 把本地 `app.py` 暴露成公网 HTTPS 地址，这样手机浏览器才能正常触发相机权限并加载页面。

如果你直接用 `http://局域网IP:7898` 打开，有些浏览器会禁止/限制相机相关能力，导致 A 端一直扫不到。

## 最快启动方式（推荐从这里开始）
1. 安装 Python 依赖（在 `\project` 目录执行）
```bash
pip install flask flask-socketio eventlet
```

2. 启动后端（另开一个终端保持运行）
```bash
python app.py
```

3. 安装并运行 Cloudflared
   - 下载 `cloudflared`
     - Windows：后解压，得到 `cloudflared.exe`
     - Linux：通常是 `cloudflared-linux-amd64` 之类的二进制；解压后进入目录，确保有执行权限（`chmod +x cloudflared`）


   - 确保终端能执行它（两种方式任选其一）
     - 把 `cloudflared.exe` 放到系统 PATH 可找到的目录，或

     ```
     # 下载
     wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64

     # 添加可执行权限
     chmod +x cloudflared-linux-amd64

     # 移动到 PATH 路径下，方便全局使用
     sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

     # 运行
     cloudflared tunnel --url http://localhost:7898
     ```

     ​

     - 每次直接使用绝对路径（||`213`）

     ```
     # windows
     *:\****\cloudflared.exe ...

     # Linux
     # 赋予执行权限
     chmod +x cloudflared-linux-amd64

     # 运行隧道命令
     ./cloudflared-linux-amd64 tunnel --url http://localhost:7898
     ```

     ​

   - 运行下面命令（另开一个终端保持运行）
```bash
cloudflared tunnel --url http://localhost:7898
```

4. 在手机浏览器打开命令输出的公网 HTTPS 地址
   - 在终端里通常会出现类似：`https://xxxx.trycloudflare.com`（以实际输出为准）
   - 用这个 HTTPS 地址分别打开页面，执行 A/B 操作即可

## 一句话说明
在两台设备上打开同一个页面：A 端扫码（二维码），B 端实时收到结果，并在识别为 `http/https` 链接时自动跳转到对应页面。

## 实现功能
1. **A 端（扫码端）**
   - 打开摄像头
   - 识别**二维码**
   - 扫描成功后把识别内容通过 `Socket.IO` 发送给服务端
   - A 端仅展示“扫码成功”和扫码数据，不负责展示/跳转

2. **B 端（接收端）**
   - 监听服务端广播的 `sync_data` 事件
   - 展示识别结果（仿微信扫一扫风格：链接卡片 / 文本卡片）
   - 若识别内容是 `http/https` 链接：显示“正在跳转...”并自动 `window.location` 跳转

3. **服务端（Flask + Flask-SocketIO）**
   - `GET /` 返回页面 `templates/index.html`
   - `sync_data` 事件接收 A 端数据，并 `socketio.emit` 广播给所有连接客户端

## 目录与关键文件
- `app.py`：Flask/SocketIO 服务端逻辑
- `templates/index.html`：前端页面（A/B 逻辑、扫码与展示、页面跳转）

## 快速开始
1. 启动服务（运行 `app.py`）
2. 安装并启动 `cloudflared`，使用命令输出的公网 HTTPS 地址访问页面（例如：`https://xxxx.trycloudflare.com`）
3. 在一台设备点 **“我是 A端 (扫码)”**
4. 在另一台设备点 **“我是 B端 (接收)”**
5. A 端对准二维码，B 端会自动展示结果并跳转链接

## 使用规则（A/B 角色）
- 页面内部用 `currentRole` 区分角色：
  - 点 A：`currentRole = 'A'`
  - 点 B：`currentRole = 'B'`
- `socket.on('sync_data')` 收到广播后：
  - `currentRole !== 'B'` 时直接返回（A 端忽略广播）
  - 只有 B 端才会展示并可能执行跳转

## 识别逻辑与跳转逻辑
1. 扫描内容获取：`html5-qrcode` 的 `onDecoded(decodedText)`
2. A 端发送格式：`socket.emit('sync_data', { message: decodedText })`
3. B 端解析：
   - `parseWebUrl()` 判断 `message` 是否为 `http/https` 链接（或常见域名形式）
   - 链接：渲染“网页卡片”，并在 80ms 后执行 `window.location.href = url.href`
   - 纯文本：渲染“文本卡片”，不跳转

## 摄像头与扫描框（关于速度/识别率）
- 扫描框由 `qrbox` 控制：当前策略是**宽度尽量铺满预览宽度**，高度会按像素面积上限做缩放，避免 iPhone 等设备因解码区域过大而一直识别失败。
- 扫描性能还受以下因素影响：
  - 网络访问方式（iOS 通常对非 HTTPS 更挑）
  - 光线、二维码大小与清晰度
  - 浏览器对摄像头输出分辨率的实际选择

## 常见排查
1. **服务端终端没有打印 `收到数据:`**
   - 大概率是 A 端没有成功触发 `onDecoded`（识别失败 / 摄像头没权限 / Socket 没连上）

2. **B 端没反应**
   - 确认点了 B：`currentRole` 必须为 `'B'`

3. **iPhone 扫不到**
   - 建议用 `Chrome/Edge`（若可）或尽量使用 `https/localhost`
   - 让二维码占画面更大，光线更均匀

## 后续可选增强
- 支持更多识别类型（如条形码、EAN/Code128 等）需要扩展扫码库配置或增加解码器
- 让 B 端选择“新标签页打开”而不是当前页跳转
- 为 A/B 分别做更细的相机策略（不同浏览器/机型单独参数）

