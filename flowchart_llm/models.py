from pydantic import BaseModel, Field
from typing import List, Optional

class Node(BaseModel):
    id: str
    text: str
    type: str  # e.g., "start", "end", "process", "decision", "input/output"

class Edge(BaseModel):
    id: str
    source: str  # Node ID
    target: str  # Node ID
    label: Optional[str] = None

class Flowchart(BaseModel):
    nodes: List[Node]
    edges: List[Edge]