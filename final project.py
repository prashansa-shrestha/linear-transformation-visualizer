### main.py
from cube import get_unit_cube_vertices, cube_edges
from transform import apply_matrix, interpolate_vertices
from draw import draw_cube
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    gluPerspective(45, (800 / 600), 0.1, 50.0)
    glTranslatef(-0.5, -0.5, -5)  # center cube on screen

    original = get_unit_cube_vertices()

    # Example transformation matrix
    transformation_matrix = np.array([
        [1.5, 0.5, 0],
        [0, 1.5, 0],
        [0, 0, 1]
    ])

    determinant = np.linalg.det(transformation_matrix)
    print(f"Determinant (volume scaling factor): {determinant:.2f}")

    transformed = apply_matrix(transformation_matrix, original)

    clock = pygame.time.Clock()
    t = 0.0
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        t = min(t + 0.01, 1.0)
        current = interpolate_vertices(original, transformed, t)

        draw_cube(original, cube_edges, color=(0.5, 0.5, 0.5))   # original (gray)
        draw_cube(current, cube_edges, color=(1, 0, 0))         # transformed (red)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()




