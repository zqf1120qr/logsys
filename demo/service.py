from database import HugeGraphClient
from analyzer import LLMAnalyzer

class GraphBuilderService:
    """系统核心业务逻辑层 (终极修复版)"""
    
    def __init__(self):
        self.db = HugeGraphClient(
            host="127.0.0.1",  # 确保是你的真实 IP
            port=8080,
            graph="hugegraph"
        )
        self.analyzer = LLMAnalyzer()

    def initialize_system(self) -> str:
        try:
            self.db.init_schema()
            return "HugeGraph Schema 初始化成功。"
        except Exception as e:
            return f"Schema 初始化可能已存在: {str(e)}"

    def build_ontology_graph(self, doc_text: str) -> tuple[dict, list]:
        """构建静态本体图谱"""
        arch_data = self.analyzer.analyze_architecture(doc_text)
        execution_logs = []
        
        # 【修复核心】用字典记住数据库返回的真实 ID：{"API-Gateway": "5:API-Gateway"}
        real_id_map = {}
        
        # 1. 写入核心服务节点，并记录真实 ID
        for svc in arch_data.get("services", []):
            name = svc['name']
            res = self.db.add_vertex("Service", {"name": name, "layer_type": svc.get('layer', 'unknown')})
            if "id" in res:
                real_id_map[name] = res["id"]
                execution_logs.append(f"🟢 写入节点: {name} (真实ID: {res['id']})")
            
        # 2. 准备连线，并动态补全缺失的组件节点
        for call in arch_data.get("calls", []):
            source = call['source']
            target = call['target']
            
            # 补全源节点
            if source not in real_id_map:
                res = self.db.add_vertex("Service", {"name": source, "layer_type": "Component"})
                real_id_map[source] = res.get("id")
                execution_logs.append(f"🟡 补全节点: {source}")
                
            # 补全目标节点
            if target not in real_id_map:
                res = self.db.add_vertex("Service", {"name": target, "layer_type": "Component"})
                real_id_map[target] = res.get("id")
                execution_logs.append(f"🟡 补全节点: {target}")
                
            # 3. 双方真实 ID 都拿到了，安全连线！
            out_vid = real_id_map.get(source)
            in_vid = real_id_map.get(target)
            
            if out_vid and in_vid:
                self.db.add_edge("CALLS", out_vid, in_vid)
                execution_logs.append(f"🔗 写入连线: {source} -[CALLS]-> {target}")
            
        return arch_data, execution_logs

    def build_mechanism_graph(self, log_text: str) -> tuple[dict, list]:
        """构建动态机理故障图谱"""
        log_data = self.analyzer.analyze_logs(log_text)
        execution_logs = []
        logs = log_data.get("logs", [])
        
        prev_real_log_id = None
        
        for i, log in enumerate(logs):
            service_name = log.get('service', 'Unknown')
            
            # 1. 写入 LogEvent 节点并获取真实 ID
            res_log = self.db.add_vertex("LogEvent", {
                "trace_id": log.get('trace_id', 'T1'),
                "timestamp": log.get('timestamp', '0'),
                "level": log.get('level', 'INFO'),
                "message": log.get('message', '')
            })
            real_log_id = res_log.get("id")
            
            # 2. 【修复核心】向 HugeGraph 再次推送一次 Service 节点。
            # HugeGraph 的主键策略特性：如果节点已存在，它不会报错，而是直接返回存在的那个节点的真实 ID！
            res_svc = self.db.add_vertex("Service", {"name": service_name, "layer_type": "Component"})
            real_svc_id = res_svc.get("id")
            
            # 3. 挂载到本体图谱
            if real_log_id and real_svc_id:
                self.db.add_edge("OCCURRED_ON", real_log_id, real_svc_id)
                execution_logs.append(f"🔴 日志挂载成功: [Log] -> [Service:{service_name}]")
            
            # 4. 时序连线
            if prev_real_log_id and real_log_id:
                self.db.add_edge("PRECEDES", prev_real_log_id, real_log_id)
            
            prev_real_log_id = real_log_id
            
        return log_data, execution_logs