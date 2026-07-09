import requests

class HugeGraphClient:
    """封装 HugeGraph REST API 的数据访问层 (DAO)"""
    
    def __init__(self, host="127.0.0.1", port=8080, graph="hugegraph"):
        self.base_url = f"http://{host}:{port}/graphs/{graph}"
        self.headers = {"Content-Type": "application/json"}

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}/{path}"
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code not in [200, 201, 202]:
            raise Exception(f"HugeGraph API 错误 [{response.status_code}]: {response.text}")
        return response.json()

    def init_schema(self):
        """初始化图模式 (Schema)"""
        properties = [
            {"name": "name", "data_type": "TEXT", "cardinality": "SINGLE"},
            {"name": "layer_type", "data_type": "TEXT", "cardinality": "SINGLE"},
            {"name": "timestamp", "data_type": "TEXT", "cardinality": "SINGLE"},
            {"name": "level", "data_type": "TEXT", "cardinality": "SINGLE"},
            {"name": "trace_id", "data_type": "TEXT", "cardinality": "SINGLE"},
            {"name": "message", "data_type": "TEXT", "cardinality": "SINGLE"}
        ]
        for prop in properties:
            self._post("schema/propertykeys", prop)

        self._post("schema/vertexlabels", {
            "name": "Service", "id_strategy": "PRIMARY_KEY",
            "primary_keys": ["name"], "properties": ["name", "layer_type"]
        })
        self._post("schema/vertexlabels", {
            "name": "LogEvent", "id_strategy": "PRIMARY_KEY",
            "primary_keys": ["trace_id", "timestamp"], "properties": ["trace_id", "timestamp", "level", "message"]
        })

        edges = [
            {"name": "CALLS", "source_label": "Service", "target_label": "Service"},
            {"name": "OCCURRED_ON", "source_label": "LogEvent", "target_label": "Service"},
            {"name": "PRECEDES", "source_label": "LogEvent", "target_label": "LogEvent"}
        ]
        for edge in edges:
            self._post("schema/edgelabels", edge)

    def add_vertex(self, label: str, properties: dict):
        """向图数据库插入一个顶点"""
        return self._post("graph/vertices", {"label": label, "properties": properties})

    def add_edge(self, label: str, out_v: str, in_v: str, properties: dict = None):
        """向图数据库插入一条边 (智能推断标签版)"""
        
        # 核心修复：根据我们要画的边的名字，智能推断出起点和终点应该叫什么标签
        if label == "CALLS":
            out_label = "Service"
            in_label = "Service"
        elif label == "OCCURRED_ON":
            out_label = "LogEvent"
            in_label = "Service"
        elif label == "PRECEDES":
            out_label = "LogEvent"
            in_label = "LogEvent"
        else:
            out_label = "Service"
            in_label = "Service" # 默认兜底
            
        payload = {
            "label": label, 
            "outV": out_v, 
            "inV": in_v,
            "outVLabel": out_label, 
            "inVLabel": in_label,
            "properties": properties or {}
        }
        return self._post("graph/edges", payload)