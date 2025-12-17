class DobotGrid:
    def __init__(self, port="/dev/ttyACM0"):
        print("INITIALIZING DOBOT")

    def generate_points(self):
        print("Grid points generated successfully.")

    def generate_grid(self):
        print("Grid coordinates generated successfully.")

    def move_to_point(self, key, delay=0):
        if key.lower() == "home":
            print("Moving to home position.")
        print(f"Moving to {key} position")
    
    def move_to_intermediate(self):
        print(f"Moving to intermdiate position")

    def draw_grid(self):
        print("Grid drawing completed successfully!")
    
    def draw_x(self, row, col, delay=0):
        print("drawing x")

    def draw_o(self, row, col, angle_step=25):
        print("drawing o")
    
    def disconnect(self):
        print("diconnected")
