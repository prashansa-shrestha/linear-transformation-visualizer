### transform.py
import numpy as np

def apply_matrix(matrix, vertices):
    transformed = []
    for v in vertices:
        vec = np.array(v)
        new_v = matrix @ vec
        transformed.append(new_v.tolist())
    return transformed

def lerp(v1, v2, t):
    return [v1[i] + (v2[i] - v1[i]) * t for i in range(3)]

def interpolate_vertices(v1, v2, t):
    return [lerp(a, b, t) for a, b in zip(v1, v2)]

