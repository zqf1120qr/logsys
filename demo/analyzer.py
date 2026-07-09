from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class LLMAnalyzer:
    """封装大模型交互的 AI 解析层"""
    
    def __init__(self, base_url="http://localhost:1234/v1", api_key="not-needed"):
        # 接入本地大模型 (llama.cpp 等)
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            temperature=0.1
        )
        self.parser = JsonOutputParser()

    def analyze_architecture(self, text: str) -> dict:
        """从非结构化文档提取架构实体与关系"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个资深的微服务架构分析师。请提取架构信息，并严格以JSON格式输出。
                必须包含以下两个数组：
                1. 'services' (包含所有节点，字段: name, layer)。
                ⚠️ 核心规则：如果你在文中发现了任何数据库、缓存、中间件（如 Redis、MySQL 等），它们也属于系统节点！你必须将它们作为一个独立的对象加入到 'services' 数组中，并将其 layer 字段设为 'Component层'。
                2. 'calls' (包含所有依赖调用关系，字段: source, target)。如果有服务依赖数据库或缓存，请在此处建立连线。
                确保 calls 中出现的所有 source 和 target 名称，都必须在 services 数组中存在！"""),
            ("user", "{text}")
        ])
        chain = prompt | self.llm | self.parser
        return chain.invoke({"text": text})

    def analyze_logs(self, text: str) -> dict:
        """从非结构化日志提取故障链路"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个故障诊断专家。请提取日志中的链路信息，并严格以JSON格式输出。包含一个数组 'logs'，每个元素需提取字段：trace_id, timestamp, service, level, message。"),
            ("user", "{text}")
        ])
        chain = prompt | self.llm | self.parser
        return chain.invoke({"text": text})