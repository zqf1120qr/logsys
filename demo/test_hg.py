# 创建一个 test_write.py
from database import HugeGraphClient

# 填入你确认无误的 IP
client = HugeGraphClient(host="127.0.0.1", port=8080, graph="hugegraph")
# 尝试写入一个顶点
try:
    res = client.add_vertex("Service", {"name": "Test-Service", "layer_type": "Gateway"})
    print("写入结果:", res)
except Exception as e:
    print("写入失败:", e)