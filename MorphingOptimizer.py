from tkinter.constants import NO
import gurobipy as gp
from gurobipy import GRB
import numpy as np


class MorphingOptimizer:
    def __init__(self, src_points, dst_points) -> None:
        self.src_points = src_points
        self.dst_points = dst_points

        self.distances_matrix = np.zeros(shape=(len(src_points),
                                                len(dst_points)))
        for i, src_p in enumerate(src_points):
            for j, dst_p in enumerate(dst_points):
                self.distances_matrix[i, j] = np.linalg.norm(
                    np.array(src_p) - np.array(dst_p))

        self.ns = len(self.src_points)
        self.nd = len(self.dst_points)
        self.N = max(self.ns, self.nd)

    def build(self):
        self.model = gp.Model("MorphMatching")

        # Variables
        self.matching = self.model.addMVar((self.N, self.N), vtype=GRB.BINARY)

        if self.ns < self.nd:
            self.s = self.model.addMVar((self.nd - self.ns, self.ns),
                                        vtype=GRB.BINARY)

        elif self.ns > self.nd:
            self.s = self.model.addMVar((self.ns - self.nd, self.nd),
                                        vtype=GRB.BINARY)

        # Constraints
        self.model.addConstrs(self.matching[:, j].sum() == 1
                              for j in range(self.nd))
        self.model.addConstrs(self.matching[i, :].sum() == 1
                              for i in range(self.ns))

        if self.ns < self.nd:
            self.model.addConstrs(self.s[k, :].sum() == 1
                                  for k in range(self.nd - self.ns))
        elif self.ns > self.nd:
            self.model.addConstrs(self.s[k, :].sum() == 1
                                  for k in range(self.ns - self.nd))

        # Objective
        additional = 0
        if self.ns < self.nd:
            additional = sum(self.distances_matrix[i, j] *
                             self.matching[k + self.ns, j] * self.s[k, i]
                             for k in range(self.nd - self.ns)
                             for i in range(self.ns) for j in range(self.nd))
        elif self.ns > self.nd:
            additional = sum(self.distances_matrix[i, j] *
                             self.matching[i, k + self.nd] * self.s[k, j]
                             for k in range(self.ns - self.nd)
                             for i in range(self.ns) for j in range(self.nd))

        self.model.setObjective(
            sum(self.distances_matrix[i, j] * self.matching[i, j]
                for i in range(self.ns)
                for j in range(self.nd)) + additional, GRB.MINIMIZE)

    def solve(self):
        self.model.optimize()
        self.matching = self.matching.X
        self.copies = self.s.X if hasattr(self, 's') else None


if __name__ == "__main__":
    d = np.array([[0.4, 1.2, 4.0], [0.6, 0.8, 2.4], [0.7, 0.2, 0.9]])
    solver = MorphingOptimizer(d)
    solver.build()
    solver.solve()