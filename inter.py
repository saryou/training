from typing import List, Optional
import re


_spaces = re.compile('\s')


def is_space(char: str) -> bool:
    return bool(char and _spaces.match(char))


class Source:
    def __init__(self, src: str) -> None:
        self.src = src
        self.index = 0
        self.stack: List[int] = []

    def next(self):
        self.index += 1

    def peek(self) -> Optional[str]:
        if len(self.src) <= self.index:
            return None
        return self.src[self.index]

    def peek_char(self) -> Optional[str]:
        self.save()
        self.skip_spaces()
        result = self.peek()
        self.restore()
        return result

    def skip_spaces(self):
        while is_space(self.peek()):
            self.next()

    def save(self):
        self.stack.append(self.index)

    def restore(self):
        self.index = self.stack.pop()

    def advance(self):
        self.stack.pop()

    def __enter__(self):
        self.save()

    def __exit__(self, exc_type, exc_value, traceback):
        if isinstance(exc_value, ParseError):
            self.restore()
        else:
            self.advance()
        return False

    def __repr__(self) -> str:
        return f'''
src: {self.src}
index: {self.index}
stack: {self.stack}
'''


class ParseError(Exception):
    def __init__(self, src: Source, msg: str='no message') -> None:
        self.src = src
        self.msg = msg


class Node:
    def __init__(self, children: List['Node']) -> None:
        self.children = children

    def append(self, node: 'Node'):
        self.children.append(node)

    def eval(self):
        pass

    @classmethod
    def parse(cls, src: Source) -> 'Node':
        pass


class ExpressionNode(Node):
    def eval(self):
        result = 0
        for (sign, node) in zip(self.children[0::2], self.children[1::2]):
            if sign.eval() == '+':
                result += node.eval()
            elif sign.eval() == '-':
                result -= node.eval()
        return result

    @classmethod
    def parse(cls, src: Source) -> Node:
        children: List[Node] = []
        if src.peek_char() not in {'+', '-'}:
            children.append(CharNode('+'))
            children.append(TermNode.parse(src))
        while src.peek_char() in {'+', '-'}:
            children.append(CharNode.parse(src))
            children.append(TermNode.parse(src))
        return ExpressionNode(children)

    def __repr__(self) -> str:
        return ' '.join(str(c) for c in self.children)


class TermNode(Node):
    def eval(self):
        result = self.children[0].eval()
        for (sign, node) in zip(self.children[1::2], self.children[2::2]):
            if sign.eval() == '*':
                result *= node.eval()
            elif sign.eval() == '/':
                result /= node.eval()
        return result

    @classmethod
    def parse(cls, src: Source) -> Node:
        children: List[Node] = [FactorNode.parse(src)]
        while src.peek_char() in {'*', '/'}:
            children.append(CharNode.parse(src))
            children.append(FactorNode.parse(src))
        return TermNode(children)

    def __repr__(self) -> str:
        return ' '.join(str(c) for c in self.children)


class FactorNode(Node):
    def eval(self):
        return self.children[0].eval()

    @classmethod
    def parse(cls, src: Source) -> Node:
        try:
            with src:
                if CharNode.parse(src).eval() != '(':
                    raise ParseError(src)
                exp = ExpressionNode.parse(src)
                if CharNode.parse(src).eval() != ')':
                    raise ParseError(src)
            return FactorNode([exp])
        except ParseError:
            return FactorNode([NumberNode.parse(src)])

    def __repr__(self) -> str:
        c = self.children[0]
        return f'({c})' if isinstance(c, ExpressionNode) else str(c)


class NumberNode(Node):
    numbers = {str(i) for i in range(10)}

    def eval(self):
        return int(''.join([c.eval() for c in self.children]))

    @classmethod
    def parse(cls, src: Source) -> Node:
        numbers: List[Node] = []
        while src.peek_char() in cls.numbers:
            numbers.append(CharNode.parse(src))
        if not numbers:
            raise ParseError(src, f'`{src.peek_char()}` is not a number.')
        return NumberNode(numbers)

    def __repr__(self) -> str:
        return str(self.eval())


class CharNode(Node):
    def __init__(self, char: str) -> None:
        super().__init__([])
        self.char = char

    def eval(self):
        return self.char

    @classmethod
    def parse(cls, src: Source) -> Node:
        src.skip_spaces()
        char = src.peek()
        if not char:
            raise ParseError(src, 'index out of range')
        src.next()
        return CharNode(char)

    def __repr__(self) -> str:
        return self.char


def parse(text: str) -> Node:
    src = Source(text)
    expr = ExpressionNode.parse(src)
    if src.peek_char() is not None:
        raise ParseError(src, f'unexpected character `{src.peek_char()}` found')
    return expr


expr = parse('12*5+ (2+3) *10+20/02')
print(expr)
print(expr.eval())
expr = parse('- (20 - 10) ')
print(expr)
print(expr.eval())
expr = parse('-20 + 10)')
print(expr)
print(expr.eval())