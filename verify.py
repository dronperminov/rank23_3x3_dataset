import json
import re
import sys
from fractions import Fraction
from typing import List, Tuple, Union


class Scheme:
    def __init__(self, dimension: Tuple[int, int, int], rank: int, u: List[list], v: List[list], w: List[list]) -> None:
        self.dimension = dimension
        self.elements = tuple(dimension[i] * dimension[(i + 1) % 3] for i in range(3))
        self.rank = rank
        self.u = u
        self.v = v
        self.w = w

        assert len(u) == len(v) == len(w) == rank
        assert len(u[0]) == self.elements[0]
        assert len(v[0]) == self.elements[1]
        assert len(w[0]) == self.elements[2]

    @classmethod
    def load(cls, path: str) -> "Scheme":
        lower_path = path.lower()

        if lower_path.endswith(".txt"):
            return Scheme.from_txt(path)

        if lower_path.endswith(".m"):
            return Scheme.from_m(path)

        if lower_path.endswith(".json"):
            return Scheme.from_json(path)

        raise ValueError(f'Invalid extension "{path}"')

    @classmethod
    def from_json(cls, path: str) -> "Scheme":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        n1, n2, n3 = data["dimension"]
        rank = data["rank"]
        u = [[cls.__parse_value(value) for value in row] for row in data["u"]]
        v = [[cls.__parse_value(value) for value in row] for row in data["v"]]
        w = [[cls.__parse_value(value) for value in row] for row in data["w"]]
        return Scheme(dimension=(n1, n2, n3), rank=rank, u=u, v=v, w=w)

    @classmethod
    def from_m(cls, path: str) -> "Scheme":
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        text = text.replace("{", "[").replace("}", "]")
        text = re.sub(r"(-?\d+/\d+)", r'"\1"', text)
        data = json.loads(text)

        dimension = len(data[0][0]), len(data[0][1]), len(data[0][1][0])

        u, v, w = [], [], []
        for index, (ui, vi, wi) in enumerate(data):
            u.append([cls.__parse_value(value) for row in ui for value in row])
            v.append([cls.__parse_value(value) for row in vi for value in row])
            w.append([cls.__parse_value(value) for row in wi for value in row])

        return Scheme(dimension=dimension, rank=len(data), u=u, v=v, w=w)

    @classmethod
    def from_txt(cls, path: str) -> "Scheme":
        with open(path) as f:
            text = " ".join([line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")])
            text = map(int, re.split(r"[\s\n]+", text))

        n1, n2, n3, rank, *uvw = text
        elements = [n1 * n2, n2 * n3, n3 * n1]
        k = 2 if path.endswith("_Q.txt") else 1

        u_values = uvw[:elements[0] * rank * k]
        v_values = uvw[elements[0] * rank * k:(elements[0] + elements[1]) * rank * k]
        w_values = uvw[(elements[0] + elements[1]) * rank * k:]

        u, v, w = [], [], []
        for index in range(rank):
            offsets = [index * elements[i] for i in range(3)]

            if k == 2:
                u.append([Fraction(u_values[(offsets[0] + i) * 2], u_values[(offsets[0] + i) * 2 + 1]) for i in range(elements[0])])
                v.append([Fraction(v_values[(offsets[1] + i) * 2], v_values[(offsets[1] + i) * 2 + 1]) for i in range(elements[1])])
                w.append([Fraction(w_values[(offsets[2] + i) * 2], w_values[(offsets[2] + i) * 2 + 1]) for i in range(elements[2])])
            else:
                u.append([u_values[offsets[0] + i] for i in range(elements[0])])
                v.append([v_values[offsets[1] + i] for i in range(elements[1])])
                w.append([w_values[offsets[2] + i] for i in range(elements[2])])

        return Scheme(dimension=(n1, n2, n3), rank=rank, u=u, v=v, w=w)

    def validate(self) -> bool:
        for i in range(self.elements[0]):
            for j in range(self.elements[1]):
                for k in range(self.elements[2]):
                    if not self.__validate_equation(i, j, k):
                        return False

        return True

    def __validate_equation(self, i: int, j: int, k: int) -> bool:
        i1, i2 = i // self.dimension[1], i % self.dimension[1]
        j1, j2 = j // self.dimension[2], j % self.dimension[2]
        k1, k2 = k // self.dimension[0], k % self.dimension[0]

        target = (i2 == j1) and (i1 == k2) and (j2 == k1)
        equation = sum(self.u[index][i] * self.v[index][j] * self.w[index][k] for index in range(self.rank))
        return equation == target

    @staticmethod
    def __parse_value(value: Union[str, int, Fraction]) -> Union[int, Fraction]:
        if isinstance(value, str):
            value = Fraction(value)

        if isinstance(value, Fraction) and value.denominator == 1:
            value = int(value)

        return value


def main():
    print("Loading dataset...")
    with open("dataset.json", "r") as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} rank patterns, validating schemes...")

    failed = []

    for i, (pattern, data) in enumerate(dataset.items(), start=1):
        filename = data["filename"]

        for extension in ["json", "m", "txt"]:
            scheme_path = f"schemes/{pattern}/{filename}.{extension}"
            scheme = Scheme.load(scheme_path)

            if not scheme.validate():
                failed.append(f"{scheme_path}: Brent equations are not satisfied")

        if i % 1000 == 0 or i == len(dataset):
            print(f"{i} / {len(dataset)} rank patterns checked")

    if failed:
        print(f"{len(failed)} problems found:")
        for message in failed:
            print(f"  - {message}")

        sys.exit(1)

    print("All schemes are valid")


if __name__ == '__main__':
    main()
