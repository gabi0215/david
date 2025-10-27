from typing import Any, Optional, Iterator

class _Node:
    def __init__(self, value: Any, next: Optional['_Node'] = None) -> None:
        self.value = value
        self.next = next
        
class LinkedList:
    """단순 연결리스트: 임의 위치 삽입/삭제, 리스트 변환, 길이."""

    def __init__(self) -> None:
        self._head: Optional[_Node] = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def _iter_nodes(self) -> Iterator[_Node]:
        cur = self._head
        while cur is not None:
            yield cur
            cur = cur.next

    def to_list(self) -> list:
        return [n.value for n in self._iter_nodes()]

    def insert(self, index: int, value: Any) -> None:
        """0 <= index <= len(self) 위치에 삽입. 범위 밖이면 IndexError."""
        if index < 0 or index > self._size:
            raise IndexError('index out of range')

        node = _Node(value)
        if index == 0:
            node.next = self._head
            self._head = node
        else:
            prev = self._head
            for _ in range(index - 1):
                assert prev is not None  # for type checker
                prev = prev.next
            node.next = prev.next  # type: ignore[union-attr]
            prev.next = node       # type: ignore[union-attr]
        self._size += 1

    def delete(self, index: int) -> Any:
        """해당 위치 노드 삭제 후 값을 반환. 범위 밖이면 IndexError."""
        if index < 0 or index >= self._size:
            raise IndexError('index out of range')

        if index == 0:
            assert self._head is not None
            removed = self._head
            self._head = removed.next
        else:
            prev = self._head
            for _ in range(index - 1):
                assert prev is not None
                prev = prev.next
            assert prev is not None and prev.next is not None
            removed = prev.next
            prev.next = removed.next

        self._size -= 1
        return removed.value


class CircularList:
    """원형 연결리스트(단일 연결): 커서 기반 삽입, 값 삭제, 순환 이동, 검색."""

    def __init__(self) -> None:
        self._cursor: Optional[_Node] = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, value: Any) -> None:
        """
        비었으면 단일 노드 원형 구성.
        아니면 커서 뒤에 삽입 후 커서를 새 노드로 이동.
        """
        node = _Node(value)
        if self._cursor is None:
            node.next = node
            self._cursor = node
            self._size = 1
            return

        node.next = self._cursor.next
        self._cursor.next = node
        self._cursor = node
        self._size += 1

    def delete(self, value: Any) -> bool:
        """
        값이 같은 '첫' 노드를 삭제.
        - 성공 시 True, 없으면 False.
        - 삭제 노드가 커서면 커서를 이전 노드로 이동.
        - 노드가 1개뿐이고 그것을 삭제하면 빈 상태가 됨.
        """
        cur = self._cursor
        if cur is None:
            return False

        prev = cur
        cur = cur.next  # 탐색 시작점: 커서 다음
        for _ in range(self._size):
            assert prev is not None and cur is not None
            if cur.value == value:
                if self._size == 1:
                    self._cursor = None
                    self._size = 0
                    return True

                # 제거 연결
                prev.next = cur.next
                # 커서 정정: 삭제되는 노드가 커서일 때 이전 노드로 이동
                if cur is self._cursor:
                    self._cursor = prev
                self._size -= 1
                return True
            prev, cur = cur, cur.next  # 다음 노드로

        return False

    def get_next(self) -> Optional[Any]:
        """비었으면 None. 아니면 커서를 다음 노드로 이동 후 그 값을 반환(순환)."""
        if self._cursor is None:
            return None
        self._cursor = self._cursor.next  # type: ignore[union-attr]
        return self._cursor.value  # type: ignore[union-attr]

    def search(self, value: Any) -> bool:
        """값 존재 여부를 반환."""
        cur = self._cursor
        if cur is None:
            return False
        cur = cur.next
        for _ in range(self._size):
            assert cur is not None
            if cur.value == value:
                return True
            cur = cur.next
        return False

    def to_list_once(self, limit: Optional[int] = None) -> list:
        """
        디버깅/시연용: 현재 커서 다음부터 한 바퀴(or limit개) 값을 리스트로 반환.
        (채점에는 사용되지 않음)
        """
        if self._cursor is None:
            return []
        result = []
        cur = self._cursor.next
        steps = 0
        while True:
            assert cur is not None
            result.append(cur.value)
            steps += 1
            cur = cur.next
            if cur is self._cursor.next:
                break
            if limit is not None and steps >= limit:
                break
        return result


def main() -> None:
    # 예시 시연 (PDF의 예시 흐름과 유사하되, 출력 형식은 자유)
    # Singly Linked List
    sll = LinkedList()
    print(len(sll))
    sll.insert(0, 'A')
    sll.insert(1, 'B')
    sll.insert(1, 'C')
    print(sll.to_list())
    print(sll.delete(1))
    print(sll.to_list())
    print(len(sll))

    # Circular Linked List
    cll = CircularList()
    print(cll.get_next())         # None (빈 리스트)
    cll.insert('A')
    cll.insert('B')
    cll.insert('C')
    print(cll.delete('B'))        # True
    print(cll.search('B'))        # False
    # 순환 확인: A -> C -> A -> ...
    print([cll.get_next() for _ in range(5)])
    print(cll.delete('A'))        # True
    print([cll.get_next() for _ in range(4)])
    print(cll.delete('X'))        # False


if __name__ == '__main__':
    main()
