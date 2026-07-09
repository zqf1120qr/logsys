import re

blocks, ips, relations = set(), set(), set()

with open('HDFS.log', 'r', encoding='utf-8') as f:
    for line in f.readlines():
        b_match = re.search(r'(blk_-?\d+)', line)
        if not b_match: continue
        b_id = b_match.group(1)
        blocks.add(b_id)
        
        for ip in re.findall(r'/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line):
            ips.add(ip)
            act = "RECEIVES_BLOCK" if "Receiv" in line else "SERVES_BLOCK" if "Serv" in line or "Transmitted" in line else "OPERATES_ON"
            relations.add((ip, b_id, act))

cypher = "CREATE \n"
nodes = []
block_alias = {b: f"b_{i}" for i, b in enumerate(blocks)}
ip_alias = {ip: f"n_{i}" for i, ip in enumerate(ips)}

for b, alias in block_alias.items():
    nodes.append(f"({alias}:Block {{id: '{b}'}})")
for ip, alias in ip_alias.items():
    nodes.append(f"({alias}:DataNode {{ip: '{ip}'}})")

edges = []
for ip, b, act in relations:
    edges.append(f"({ip_alias[ip]})-[:{act}]->({block_alias[b]})")

cypher += ",\n".join(nodes + edges)

with open('cypher_commands.txt', 'w', encoding='utf-8') as out:
    out.write(cypher)

