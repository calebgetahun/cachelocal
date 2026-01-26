from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")

@dataclass
class DLLNode(Generic[K, V]):
    key: Optional[K] = None
    val: Optional[V] = None
    prev: Optional["DLLNode[K, V]"] = None
    next: Optional["DLLNode[K, V]"] = None
    expires_at: Optional[float] = None  # monotonic timestamp

class DLList(Generic[K, V]):
    """Doubly-linked list for mainting insertion order. """
    
    def __init__(self):
        self.head: DLLNode[K, V] = DLLNode()
        self.tail: DLLNode[K, V] = DLLNode()

        self.head.next = self.tail
        self.tail.prev = self.head

    def add_to_front(self, node: DLLNode[K, V]) -> None:
        if node is None:
            return
        
        if node.prev is not None or node.next is not None:
            raise RuntimeError("Attempting to move a node to the front that contains next or prev linkages")
        
        node.next = self.head.next
        node.prev = self.head

        self.head.next.prev = node
        self.head.next = node

    def unlink_node(self, node: DLLNode[K, V]) -> None:
        if node is None or node is self.head or node is self.tail:
            return
        
        node.prev.next = node.next
        node.next.prev = node.prev

        node.next = None
        node.prev = None

    def pop_tail(self) -> Optional[DLLNode[K, V]]:
        if self.head.next is self.tail:
            return None
        
        to_remove = self.tail.prev
        self.unlink_node(to_remove)

        return to_remove
    
    def is_empty(self) -> bool:
        return self.head.next is self.tail