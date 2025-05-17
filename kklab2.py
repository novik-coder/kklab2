from typing import Set, List, Tuple, Dict
from collections import OrderedDict

class CFG:
    def __init__(self, nonterminals: List[str], terminals: Set[str], productions: Dict[str, List[List[str]]], start: str):
        self.N = nonterminals  # 使用列表而非集合
        self.Sigma = terminals
        self.P = productions
        self.S = start

    def __str__(self):
        result = []
        result.append(f"Nonterminals: {self.N}")
        result.append(f"Terminals: {self.Sigma}")
        result.append(f"Start symbol: {self.S}")
        result.append("Productions:")
        for head, bodies in self.P.items():
            for body in bodies:
                result.append(f"  {head} -> {' '.join(body) if body else 'ε'}")
        return "\n".join(result)

def find_nullable(cfg: CFG) -> Set[str]:
    """Find all nullable nonterminals (that can derive ε)."""
    nullable = set()
    changed = True
    while changed:
        changed = False
        for head, bodies in cfg.P.items():
            for body in bodies:
                if not body or all(symbol in nullable for symbol in body):
                    if head not in nullable:
                        nullable.add(head)
                        changed = True
    return nullable

def remove_epsilon_rules(cfg: CFG) -> CFG:
    nullable = find_nullable(cfg)
    new_productions = {}

    # Step 1: 生成所有非空组合的产生式
    for head, bodies in cfg.P.items():
        new_bodies = set()
        for body in bodies:
            positions = [i for i, symbol in enumerate(body) if symbol in nullable]
            n = len(positions)
            for mask in range(1 << n):
                new_body = body.copy()
                for j in range(n):
                    if (mask >> j) & 1:
                        new_body[positions[j]] = None
                candidate = [s for s in new_body if s is not None]
                if candidate or head == cfg.S:
                    new_bodies.add(tuple(candidate))
            new_bodies.add(tuple(body))
        # 非S的非终结符必须删除ε规则
        if head != cfg.S:
            new_bodies = {b for b in new_bodies if b}
        new_productions[head] = [list(b) for b in new_bodies]

    # Step 2: 检查S是否出现在右侧
    s_in_rhs = False
    for head, bodies in new_productions.items():
        for body in bodies:
            if cfg.S in body:
                s_in_rhs = True
                break
        if s_in_rhs:
            break

    # Step 3: 处理S → ε
    if s_in_rhs:
        # 如果S出现在右侧，完全删除所有ε规则
        if [] in new_productions[cfg.S]:
            new_productions[cfg.S].remove([])
    else:
        # 如果S未出现在右侧且原本可推导ε，则保留S → ε
        if cfg.S in nullable and [] not in new_productions[cfg.S]:
            new_productions[cfg.S].append([])

    return CFG(cfg.N, cfg.Sigma, new_productions, cfg.S)
def eliminate_left_recursion(cfg: CFG) -> CFG:
    """Устранение левой рекурсии (Общий вариант)"""
    ordered_nt = list(OrderedDict.fromkeys(cfg.N))  # 保持顺序
    new_productions = {nt: [] for nt in ordered_nt}
    new_terminals = cfg.Sigma.copy()
    new_non_terminals = cfg.N.copy()

    for i, A in enumerate(ordered_nt):
        # 替换间接左递归
        current_rules = cfg.P[A].copy()
        for j in range(i):
            B = ordered_nt[j]
            updated_rules = []
            for rule in current_rules:
                if rule and rule[0] == B:
                    updated_rules.extend([beta + rule[1:] for beta in new_productions[B]])
                else:
                    updated_rules.append(rule)
            current_rules = updated_rules

        # 分离直接左递归
        alpha, beta = [], []
        for rule in current_rules:
            (alpha if rule and rule[0] == A else beta).append(rule)

        if alpha:  # 处理直接左递归
            A_prime = A + "'"
            new_non_terminals.add(A_prime)
            new_productions[A] = [b + [A_prime] for b in beta]
            new_productions[A_prime] = [a[1:] + [A_prime] for a in alpha] + [[]]
        else:
            new_productions[A] = current_rules

    return CFG(new_non_terminals, new_terminals, new_productions, cfg.S)

# 示例输入
if __name__ == "__main__":
    # 定义一个同时包含ε规则和左递归的复杂文法
    N = {"E", "T", "F"}
    Sigma = {"+", "*", "(", ")", "id", "ε"}
    P = {
        "E": [["E", "+", "T"], ["T"], []],  # E → E+T | T | ε
        "T": [["T", "*", "F"], ["F"]],  # T → T*F | F
        "F": [["(", "E", ")"], ["id"]],  # F → (E) | id
    }
    S = "E"
    cfg = CFG(N, Sigma, P, S)

    print("=" * 50)
    print("Исходная грамматика (含ε规则和左递归):")
    print(cfg)

    # Step 1: 消除ε规则
    cfg_no_epsilon = remove_epsilon_rules(cfg)
    print("\n" + "=" * 50)
    print("Грамматика после устранения ε-правил:")
    print(cfg_no_epsilon)

    # Step 2: 消除左递归
    cfg_final = eliminate_left_recursion(cfg_no_epsilon)
    print("\n" + "=" * 50)
    print("Финальная грамматика (без ε-правил и левой рекурсии):")
    print(cfg_final)
