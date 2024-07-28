#launch.sh

# 先停止gunicorn
/flaskapp_server$ sudo kill $(lsof -i:5000|awk '{if(NR==2)print $2}')

# 再启动gunicorn
/flaskapp_server$ gunicorn --config=gunicorn_config.py main:app

https://www.cnblogs.com/Mystogan/p/16144753.html

pip install -r requirements.txt


# 启动 gunicorn 回环ip
gunicorn -w 5 -b 127.0.0.1:5000 app:app -D --timeout 3000
# 启动 gunicorn 放开所有ip
gunicorn -w 5 -b 0.0.0.0:5000 app:app -D
# 查看gunicorn的进程状态
ps aux | grep gunicorn
ps -ef | grep gunicorn

# 杀进程
lsof -i :5000
# root用户杀死占用某端口的所有进程
kill -9 $(lsof -i tcp:5000 -t)

# 非root用户杀死占用某端口的所有进程
kill -9 $(sudo lsof -i tcp:5000 -t)



# 创建新的venv
virtualenv venv
# 进入venv
source venv/bin/activate
# 退出虚拟环境
deactivate


# iptables放开端口
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 9999 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 9999 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8090 -j ACCEPT
# iptables关闭端口
sudo iptables -A OUTPUT -p udp --dport 5000 -j REJECT
sudo iptables -A OUTPUT -p tcp --dport 8090 -j REJECT
# iptables查看端口状态
iptables -L -n | grep 'tcp.*:8090'

# 备份nginx配置
cp nginx.conf nginx.conf.bak

# 测试nginx配置文件
nginx -t

# nginx启动
sudo service nginx restart



# nginx配置

