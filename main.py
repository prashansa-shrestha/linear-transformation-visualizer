import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading

class MatrixInputGUI:
    def __init__(self, callback):
        self.callback = callback
        self.matrix = None
        self.root = None
        
    def create_gui(self):
        """Create the matrix input GUI"""
        self.root = tk.Tk()
        self.root.title("Linear Transformation Matrix Input")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Enter 3x3 Transformation Matrix", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Matrix input grid
        self.entries = []
        for i in range(3):
            row_entries = []
            for j in range(3):
                entry = ttk.Entry(main_frame, width=10, font=("Arial", 12))
                entry.grid(row=i+1, column=j, padx=5, pady=5)
                if i == j:  # Set diagonal to 1 for identity matrix
                    entry.insert(0, "1")
                else:
                    entry.insert(0, "0")
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        # Preset buttons frame
        preset_frame = ttk.Frame(main_frame)
        preset_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Label(preset_frame, text="Preset Transformations:", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Preset buttons
        presets = [
            ("Identity", np.eye(3)),
            ("Scale 2x", np.diag([2, 2, 2])),
            ("Scale XY", np.diag([2, 2, 1])),
            ("Rotate Z 90°", np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])),
            ("Rotate Y 90°", np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])),
            ("Rotate X 90°", np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])),
            ("Shear X", np.array([[1, 0.5, 0], [0, 1, 0], [0, 0, 1]])),
            ("Shear Y", np.array([[1, 0, 0], [0.5, 1, 0], [0, 0, 1]])),
            ("Reflect X", np.array([[-1, 0, 0], [0, 1, 0], [0, 0, 1]])),
        ]
        
        for idx, (name, matrix) in enumerate(presets):
            row = idx // 3 + 1
            col = idx % 3
            btn = ttk.Button(preset_frame, text=name, 
                           command=lambda m=matrix: self.set_matrix(m))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Apply Transformation", 
                  command=self.apply_matrix).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Reset to Identity", 
                  command=self.reset_matrix).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=self.close_gui).grid(row=0, column=2, padx=5)
        
        # Information label
        info_text = ("The unit cube will be positioned with one corner at origin (0,0,0)\n"
                    "and extend to (1,1,1) in the first octant.\n"
                    "The entire coordinate space will transform according to your matrix.")
        info_label = ttk.Label(main_frame, text=info_text, 
                              font=("Arial", 10), foreground="gray")
        info_label.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.close_gui)
        
    def set_matrix(self, matrix):
        """Set the matrix values in the GUI"""
        for i in range(3):
            for j in range(3):
                self.entries[i][j].delete(0, tk.END)
                self.entries[i][j].insert(0, f"{matrix[i,j]:.3f}")
    
    def reset_matrix(self):
        """Reset matrix to identity"""
        self.set_matrix(np.eye(3))
    
    def apply_matrix(self):
        """Apply the current matrix"""
        try:
            matrix = np.zeros((3, 3))
            for i in range(3):
                for j in range(3):
                    value = float(self.entries[i][j].get())
                    matrix[i, j] = value
            
            # Check if matrix is invertible
            det = np.linalg.det(matrix)
            if abs(det) < 1e-10:
                messagebox.showwarning("Warning", 
                    f"Matrix is not invertible (determinant = {det:.6f})\n"
                    "The transformation will collapse the space.")
            
            self.callback(matrix)
            messagebox.showinfo("Success", "Transformation applied!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid matrix values. Please enter numbers only.")
        except Exception as e:
            messagebox.showerror("Error", f"Error applying matrix: {e}")
    
    def close_gui(self):
        """Close the GUI"""
        if self.root:
            self.root.destroy()
    
    def show(self):
        """Show the GUI"""
        self.create_gui()
        self.root.mainloop()

class LinearTransformationVisualizer:
    def __init__(self):
        self.width = 1400
        self.height = 900
        self.camera_distance = 8
        self.camera_angle_x = 25
        self.camera_angle_y = 45
        self.animation_speed = 0.015
        self.animation_progress = 0
        self.is_animating = False
        
        # Initialize font for info panel
        pygame.font.init()
        # Try to use fonts that better support Unicode characters
        try:
            self.font = pygame.font.SysFont('consolas', 16)  # Consolas has good Unicode support
        except:
            try:
                self.font = pygame.font.SysFont('dejavusans', 16)  # DejaVu Sans has excellent Unicode support
            except:
                self.font = pygame.font.SysFont('arial', 16)  # Fallback to Arial
        
        # Unit cube in first octant (from origin to (1,1,1))
        self.original_cube = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # bottom face
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]   # top face
        ])
        
        self.transformed_cube = self.original_cube.copy()
        self.current_cube = self.original_cube.copy()
        
        # Transformation matrix
        self.transform_matrix = np.eye(3)
        self.original_determinant = 1.0
        self.transformed_determinant = 1.0
        
        # Grid parameters
        self.grid_size = 8
        self.grid_spacing = 1
        self.grid_density = 20  # Number of grid lines
        
        # Original and transformed grid lines
        self.original_grid_lines = self.generate_grid_lines()
        self.transformed_grid_lines = self.original_grid_lines.copy()
        self.current_grid_lines = self.original_grid_lines.copy()
        
        # Original basis vectors
        self.original_basis = np.array([
            [2, 0, 0],  # x-axis (red) - made longer for visibility
            [0, 2, 0],  # y-axis (green)
            [0, 0, 2]   # z-axis (blue)
        ])
        
        self.transformed_basis = self.original_basis.copy()
        self.current_basis = self.original_basis.copy()
        
        # Mouse interaction
        self.mouse_drag = False
        self.last_mouse_pos = [0, 0]
        
        # GUI
        self.gui = None
        self.gui_thread = None
        
    def generate_grid_lines(self):
        """Generate grid lines for the coordinate system"""
        lines = []
        
        # Create a denser grid to show space transformation
        grid_range = self.grid_size
        step = self.grid_spacing
        
        # XY plane lines
        for i in range(-grid_range, grid_range + 1, step):
            # Lines parallel to X axis
            lines.append([[i, -grid_range, 0], [i, grid_range, 0]])
            # Lines parallel to Y axis  
            lines.append([[-grid_range, i, 0], [grid_range, i, 0]])
        
        # XZ plane lines
        for i in range(-grid_range, grid_range + 1, step):
            # Lines parallel to X axis
            lines.append([[i, 0, -grid_range], [i, 0, grid_range]])
            # Lines parallel to Z axis
            lines.append([[-grid_range, 0, i], [grid_range, 0, i]])
        
        # YZ plane lines
        for i in range(-grid_range, grid_range + 1, step):
            # Lines parallel to Y axis
            lines.append([[0, i, -grid_range], [0, i, grid_range]])
            # Lines parallel to Z axis
            lines.append([[0, -grid_range, i], [0, grid_range, i]])
        
        return np.array(lines)
        
    def init_pygame(self):
        """Initialize Pygame and OpenGL"""
        pygame.init()
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Linear Transformations Visualizer - First Octant Unit Cube")
        
        # OpenGL settings
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Set background color
        glClearColor(0.05, 0.05, 0.1, 1.0)
        
        # Set up perspective
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        
    def set_camera(self):
        """Set up camera position and orientation"""
        glLoadIdentity()
        
        # Calculate camera position
        x = self.camera_distance * math.cos(math.radians(self.camera_angle_x)) * math.sin(math.radians(self.camera_angle_y))
        y = self.camera_distance * math.sin(math.radians(self.camera_angle_x))
        z = self.camera_distance * math.cos(math.radians(self.camera_angle_x)) * math.cos(math.radians(self.camera_angle_y))
        
        gluLookAt(x, y, z, 0, 0, 0, 0, 1, 0)
        
    def draw_transformed_grid(self):
        """Draw the transformed coordinate grid"""
        glLineWidth(1)
        
        # Draw original grid lines (faded)
        glColor4f(0.3, 0.3, 0.3, 0.4)
        glBegin(GL_LINES)
        for line in self.original_grid_lines:
            glVertex3f(line[0][0], line[0][1], line[0][2])
            glVertex3f(line[1][0], line[1][1], line[1][2])
        glEnd()
        
        # Draw current (animating) grid lines
        glColor4f(0.6, 0.8, 1.0, 0.8)
        glBegin(GL_LINES)
        for line in self.current_grid_lines:
            glVertex3f(line[0][0], line[0][1], line[0][2])
            glVertex3f(line[1][0], line[1][1], line[1][2])
        glEnd()
        
        # Highlight main axes
        glLineWidth(2)
        
        # X-axis (red)
        glColor3f(1.0, 0.3, 0.3)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(self.current_basis[0][0], self.current_basis[0][1], self.current_basis[0][2])
        glEnd()
        
        # Y-axis (green)
        glColor3f(0.3, 1.0, 0.3)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(self.current_basis[1][0], self.current_basis[1][1], self.current_basis[1][2])
        glEnd()
        
        # Z-axis (blue)
        glColor3f(0.3, 0.3, 1.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(self.current_basis[2][0], self.current_basis[2][1], self.current_basis[2][2])
        glEnd()
        
        # Draw origin point
        glPointSize(8)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        
    def draw_cube(self, vertices, color=(0.5, 0.8, 1.0), alpha=0.7, wireframe=False):
        """Draw a cube with given vertices"""
        # Define cube faces
        faces = [
            [0, 1, 2, 3],  # bottom
            [4, 5, 6, 7],  # top
            [0, 1, 5, 4],  # front
            [2, 3, 7, 6],  # back
            [0, 3, 7, 4],  # left
            [1, 2, 6, 5]   # right
        ]
        
        if not wireframe:
            # Draw cube faces with transparency
            glColor4f(color[0], color[1], color[2], alpha)
            glBegin(GL_QUADS)
            for face in faces:
                for vertex in face:
                    glVertex3f(vertices[vertex][0], vertices[vertex][1], vertices[vertex][2])
            glEnd()
        
        # Draw cube edges
        glColor3f(color[0]*0.7, color[1]*0.7, color[2]*0.7)
        glLineWidth(2)
        
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # bottom face
            [4, 5], [5, 6], [6, 7], [7, 4],  # top face
            [0, 4], [1, 5], [2, 6], [3, 7]   # vertical edges
        ]
        
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3f(vertices[vertex][0], vertices[vertex][1], vertices[vertex][2])
        glEnd()
        
        # Draw vertices
        glPointSize(4)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_POINTS)
        for vertex in vertices:
            glVertex3f(vertex[0], vertex[1], vertex[2])
        glEnd()
        
    def apply_transformation(self, matrix):
        """Apply transformation matrix to cube, grid, and basis vectors"""
        self.transform_matrix = matrix
        
        # Transform cube vertices
        self.transformed_cube = np.array([matrix @ vertex for vertex in self.original_cube])
        
        # Transform basis vectors
        self.transformed_basis = np.array([matrix @ basis for basis in self.original_basis])
        
        # Transform grid lines
        self.transformed_grid_lines = np.array([
            [matrix @ line[0], matrix @ line[1]] for line in self.original_grid_lines
        ])
        
        # Calculate determinants
        self.original_determinant = np.linalg.det(np.eye(3))
        self.transformed_determinant = np.linalg.det(matrix)
        
        # Start animation
        self.animation_progress = 0
        self.is_animating = True
        
    def update_animation(self):
        """Update animation progress"""
        if self.is_animating:
            self.animation_progress += self.animation_speed
            
            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.is_animating = False
                
            # Smooth easing function
            t = self.ease_in_out(self.animation_progress)
            
            # Interpolate cube vertices
            self.current_cube = (1 - t) * self.original_cube + t * self.transformed_cube
            
            # Interpolate basis vectors
            self.current_basis = (1 - t) * self.original_basis + t * self.transformed_basis
            
            # Interpolate grid lines
            self.current_grid_lines = (1 - t) * self.original_grid_lines + t * self.transformed_grid_lines
            
    def ease_in_out(self, t):
        """Smooth easing function"""
        return t * t * (3.0 - 2.0 * t)
        
    def draw_info_panel(self):
        """Draw information panel with transformation details"""
        # Switch to 2D rendering for UI
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        
        # Draw semi-transparent background
        glColor4f(0.0, 0.0, 0.0, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(10, 20)
        glVertex2f(400, 20)
        glVertex2f(400, 260)
        glVertex2f(10, 260)
        glEnd()
        
        # Draw border
        glColor4f(0.5, 0.8, 1.0, 1.0)
        glLineWidth(2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(10, 20)
        glVertex2f(400, 20)
        glVertex2f(400, 260)
        glVertex2f(10, 260)
        glEnd()
        
        # Render text information
        glColor4f(1.0, 1.0, 1.0, 1.0)
        info_texts = [
            "Current Transformation Matrix:",
            f"╭ {self.transform_matrix[0,0]:.2f} {self.transform_matrix[0,1]:.2f} {self.transform_matrix[0,2]:.2f} ╮",
            f"│ {self.transform_matrix[1,0]:.2f} {self.transform_matrix[1,1]:.2f} {self.transform_matrix[1,2]:.2f} │",
            f"╰ {self.transform_matrix[2,0]:.2f} {self.transform_matrix[2,1]:.2f} {self.transform_matrix[2,2]:.2f} ╯",
            "",
            f"Determinant: {np.linalg.det(self.transform_matrix):6.2f}",
            "Controls:",
            "G - Open transformation matrix GUI",
            "R - Reset to identity matrix",
            "Mouse drag - Rotate view",
            "Mouse wheel - Zoom in/out"
        ]
        
        y_offset = 50
        for text in info_texts:
            text_surface = self.font.render(text, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, 'RGBA', True)
            width = text_surface.get_width()
            height = text_surface.get_height()
            
            
            glRasterPos2f(30, y_offset)
            glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            y_offset += 18
        
        glEnable(GL_DEPTH_TEST)
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
    def handle_mouse_motion(self, event):
        """Handle mouse motion for camera rotation"""
        if self.mouse_drag:
            dx = event.pos[0] - self.last_mouse_pos[0]
            dy = event.pos[1] - self.last_mouse_pos[1]
            
            self.camera_angle_y += dx * 0.5
            self.camera_angle_x += dy * 0.5
            
            # Clamp vertical angle
            self.camera_angle_x = max(-89, min(89, self.camera_angle_x))
            
        self.last_mouse_pos = event.pos
        
    def handle_mouse_button(self, event):
        """Handle mouse button events"""
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.mouse_drag = True
                self.last_mouse_pos = event.pos
            elif event.button == 4:  # Mouse wheel up
                self.camera_distance = max(3, self.camera_distance - 0.5)
            elif event.button == 5:  # Mouse wheel down
                self.camera_distance = min(20, self.camera_distance + 0.5)
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_drag = False
                
    def show_matrix_gui(self):
        """Show the matrix input GUI"""
        def gui_callback(matrix):
            self.apply_transformation(matrix)
            
        self.gui = MatrixInputGUI(gui_callback)
        self.gui_thread = threading.Thread(target=self.gui.show)
        self.gui_thread.daemon = True
        self.gui_thread.start()
        
    def run(self):
        """Main application loop"""
        self.init_pygame()
        
        clock = pygame.time.Clock()
        running = True
        
        print("Linear Transformations Visualizer - First Octant Unit Cube")
        print("=" * 60)
        print("Controls:")
        print("  G - Open transformation matrix GUI")
        print("  R - Reset to identity matrix")
        print("  Mouse drag - Rotate camera")
        print("  Mouse wheel - Zoom in/out")
        print("  ESC - Exit")
        print("\nThe unit cube starts at origin (0,0,0) extending to (1,1,1)")
        print("Watch how the entire coordinate space transforms!")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        # Show matrix GUI
                        self.show_matrix_gui()
                    elif event.key == pygame.K_r:
                        # Reset to identity
                        self.apply_transformation(np.eye(3))
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event)
                elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    self.handle_mouse_button(event)
                    
            # Update animation
            self.update_animation()
            
            # Clear screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Set up camera
            self.set_camera()
            
            # Draw scene
            self.draw_transformed_grid()
            
            # Draw original cube (semi-transparent wireframe)
            if self.is_animating or not np.allclose(self.transform_matrix, np.eye(3)):
                self.draw_cube(self.original_cube, color=(0.8, 0.8, 0.8), alpha=0.3, wireframe=True)
            
            # Draw current cube (solid)
            self.draw_cube(self.current_cube, color=(1.0, 0.6, 0.2), alpha=0.8)
            
            # Draw info panel
            self.draw_info_panel()
            
            pygame.display.flip()
            clock.tick(60)
            
        # Clean up GUI
        if self.gui:
            self.gui.close_gui()
            
        pygame.quit()

def main():
    """Main function to run the visualizer"""
    try:
        visualizer = LinearTransformationVisualizer()
        visualizer.run()
    except Exception as e:
        print(f"Error running visualizer: {e}")
        print("Make sure you have the required packages installed:")
        print("pip install pygame PyOpenGL PyOpenGL_accelerate numpy")

if __name__ == "__main__":
    main()