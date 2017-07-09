from functools import reduce
from operator import ior

from nfa import State, NFA


class Node:
    def to_nfa(self, initial) -> NFA:
        raise NotImplementedError

    def nfa(self):
        return self.to_nfa({State()})


class CharNode(Node):
    def __init__(self, char):
        self.char = char

    def __bool__(self):
        return bool(self.char)

    def __repr__(self):
        return self.char

    def to_nfa(self, initial):
        s = State()
        return NFA(initial.union([s]), initial, {
            (i, self.char): {s} for i in initial
        }, {s})


class GroupNode(Node):
    def __init__(self, node):
        self.node = node

    def __bool__(self):
        return bool(self.node)

    def __repr__(self):
        return f'({self.node})'

    def to_nfa(self, initial):
        return self.node.to_nfa(initial)


class StarNode(Node):
    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return f'{self.node}*'

    def to_nfa(self, initial):
        acceptable = initial
        nfa = self.node.to_nfa(initial)
        return NFA( nfa.states, nfa.initial, {
            **nfa.transitions,
            **{(i, ''): acceptable for i in initial},
            **{(k, ''): acceptable for k in nfa.acceptable},
        }, acceptable)


class ConcatNode(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f'{self.lhs}{self.rhs}'

    def to_nfa(self, initial):
        l = self.lhs.to_nfa(initial)
        return l + self.rhs.to_nfa(l.acceptable)


class UnionNode(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f'{self.lhs}|{self.rhs}'

    def to_nfa(self, initial):
        return self.lhs.to_nfa(initial) | self.rhs.to_nfa(initial)


class Parser:
    def __init__(self, text):
        self.text = text
        self.position = 0

    def parse(self):
        return self.union()

    @property
    def cur(self):
        if self.position < len(self.text):
            return self.text[self.position]
        return None

    def next(self):
        self.position += 1

    def union(self):
        if self.cur == '|':
            self.next()
            return UnionNode(self.epsilon(), self.union())

        node = self.concat()
        if self.cur == '|':
            self.next()
            return UnionNode(node, self.union())

        return node

    def concat(self):
        lhs = self.factor_or_star()
        rhs = self.factor_or_star()
        while rhs:
            lhs = ConcatNode(lhs, rhs)
            rhs = self.factor_or_star()
        return lhs

    def factor_or_star(self):
        factor = self.factor()
        if self.cur == '*':
            self.next()
            return StarNode(factor)
        return factor

    def factor(self):
        cur = self.cur
        if cur in {None, ')'}:
            return self.epsilon()
        elif cur == '(':
            self.next()
            re = self.union()
            assert self.cur == ')'
            self.next()
            return GroupNode(re)
        elif cur not in {'|', '*'}:
            node = CharNode(cur)
            self.next()
            return node

    def epsilon(self):
        return CharNode('')


def parse(text):
    return Parser(text).parse()


def to_nfa(text):
    return parse(text).nfa()


nfa = to_nfa('zyxwv|abcd(ef|gh)ijk*(|a|b|cd)*(||a|||b)')

print(nfa.accept('zyxwv'))
print(nfa.accept('abcdefijk'))
print(nfa.accept('abcdghijacdb'))
