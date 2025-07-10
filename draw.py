### draw.py
from OpenGL.GL import *

def draw_cube(vertices, edges, color=(1, 1, 1)):
    glColor3fv(color)
    glBegin(GL_LINES)
   