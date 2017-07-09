from threading import Lock
from collections import defaultdict
from typing import Tuple, List, Set, Dict, Optional


class IdGenerator:
    def __init__(self):
        self._id = 0
        self._lock = Lock()

    def generate(self):
        with self._lock:
            self._id += 1
            return self._id


generator = IdGenerator()


class State:
    def __init__(self, *ids) -> None:
        if ids:
            self.ids = tuple(sorted(ids))
        else:
            self.ids = (generator.generate(), )

    def __repr__(self):
        return 'S({})'.format(', '.join(str(i) for i in self.ids))

    def __eq__(self, other):
        return isinstance(other, State) and self.ids == other.ids

    def __hash__(self):
        return hash(self.ids)

    def __mul__(self, other):
        assert isinstance(other, State)
        if self == other:
            return self
        else:
            return State(*self.ids, *other.ids)

    __rmul__ = __mul__


class NFA:
    def __init__(self, states: Set[State], initial: Set[State], transitions: Dict[Tuple[State, str], Set[State]], acceptable: Set[State]) -> None:
        self.states = states
        self.initial = initial
        self.transitions = transitions
        self.acceptable = acceptable

    def transit(self, input: str):
        after = set()
        for state in self.current:
            after.update(self.transitions.get((state, input), set()))
        self.current = self._with_epsilon(after)

    def _with_epsilon(self, states):
        after = set(states)
        for state in states:
            after.update(self.transitions.get((state, ''), set()))
        if after != states:
            return self._with_epsilon(after)
        return states

    def accept(self, inputs: str) -> bool:
        self.current = self._with_epsilon(self.initial)
        for input in inputs:
            self.transit(input)
        return bool(self.current.intersection(self.acceptable))

    def __repr__(self):
        return f'''states: {self.states}
initial: {self.initial}
transitions:
''' + '\n'.join(f'    {k}: {v}' for k, v in self.transitions.items()) + f'''
acceptable: {self.acceptable}'''

    def __or__(self, other):
        assert isinstance(other, NFA)
        transitions = defaultdict(set)
        for key, value in self.transitions.items():
            transitions[key].update(value)
        for key, value in other.transitions.items():
            transitions[key].update(value)
        return NFA(
            self.states.union(other.states),
            self.initial.union(other.initial),
            transitions,
            self.acceptable.union(other.acceptable))

    def __add__(self, other):
        assert isinstance(other, NFA)
        transitions = defaultdict(set)
        for key, value in self.transitions.items():
            transitions[key].update(value)
        for key, value in other.transitions.items():
            transitions[key].update(value)
        for a in self.acceptable:
            for i in other.initial:
                transitions[(a, '')].add(i)
        return NFA(
            self.states.union(other.states),
            self.initial,
            transitions,
            other.acceptable)


s0 = State()
s1 = State()
s2 = State()
s3 = State()
s4 = State()
s5 = State()


nfa = NFA({s0, s1, s2, s3, s4, s5}, {s0}, {
    (s0, "0"): {s0},
    (s0, "1"): {s0, s1},
    (s1, "0"): {s2},
    (s2, "1"): {s3},
    (s3, "0"): {s4},
    (s4, "0"): {s5},
}, {s5})


print(nfa.accept('1111100001010100'))



