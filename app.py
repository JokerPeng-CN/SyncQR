from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# 允许跨域，防止手机访问被拦截
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    # Flask 会自动去 templates 文件夹找 index.html
    return render_template('index.html')

@socketio.on('sync_data')
def handle_scan(data):
    # 收到 A端 的数据，广播给所有连接的客户端（Flask-SocketIO 5.x 用 socketio.emit 更稳妥）
    print(f"收到数据: {data}")
    socketio.emit('sync_data', data)

if __name__ == '__main__':
    # 监听所有网卡接口，端口 7898
    socketio.run(app, host='0.0.0.0', port=7898)