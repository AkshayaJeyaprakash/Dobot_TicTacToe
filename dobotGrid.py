import time
from pydobot.dobot import MODE_PTP
import pydobot
import json
import math

class DobotGrid:
    def __init__(self, port="/dev/ttyACM0"):
        self.device = pydobot.Dobot(port=port)
        self.device.speed(100, 100)
        self.grid_map = "/home/aj/Documents/Robotics-lab/mid_term/TTT_Dobot/grid_map.json"
        self.points = {}
        self.grid = {}
        self.x = 250
        self.y = -80
        self.z = -30
        self.r = 0
        self.d = 40
        self.offset = 5
        self.radius = self.d/2 - self.offset
        # self.intermediate = (182.214, -2.686, 47.714, 15.854)
        self.intermediate = (228.106, 2.180, 44.833, 0.703)
        print("Dobot connected successfully.")

    def generate_points(self):
        x = self.x
        y = self.y
        z = self.z
        r = self.r
        d = self.d

        points = {
            "A1": (x, y, z, r),
            "A2": (x, y + 3*d, z, r),
            "A3": (x + 3*d, y, z, r),
            "A4": (x + 3*d, y + 3*d, z, r),

            "S1": (x, y + d, z, r),
            "S2": (x + 3*d, y + d, z, r),
            "S3": (x, y + 2*d, z, r),
            "S4": (x + 3*d, y + 2*d, z, r),
            "S5": (x + d, y, z, r),
            "S6": (x + d, y + 3*d, z, r),
            "S7": (x + 2*d, y, z, r),
            "S8": (x + 2*d, y + 3*d, z, r),

            "SI1": (x, y + d, z + 20, r),
            "SI2": (x + 3*d, y + d, z + 20, r),
            "SI3": (x, y + 2*d, z + 20, r),
            "SI4": (x + 3*d, y + 2*d, z + 20, r),
            "SI5": (x + d, y, z + 20, r),
            "SI6": (x + d, y + 3*d, z + 20, r),
            "SI7": (x + 2*d, y, z + 20, r),
            "SI8": (x + 2*d, y + 3*d, z + 20, r),

            "SM1": (x + d, y + d, z, r),
            "SM2": (x + d, y + 2*d, z, r),
            "SM3": (x + 2*d, y + d, z, r),
            "SM4": (x + 2*d, y + 2*d, z, r)
        }
        self.points = points
        print("Grid points generated successfully.")

    def generate_grid1(self):
        grid_map_path=self.grid_map
        if not self.points:
            raise ValueError("Please generate points before generating the grid!")

        with open(grid_map_path, "r") as f:
            grid_map = json.load(f)

        grid = {}
        offset = self.offset
        z_val = self.z
        r_val = self.r

        for grid_name, corner_keys in grid_map.items():
            if len(corner_keys) != 4:
                print(f"Grid {grid_name} does not have 4 corners, skipping.")
                continue

            try:
                p1 = self.points[corner_keys[0]]
                p2 = self.points[corner_keys[1]]
                p3 = self.points[corner_keys[2]]
                p4 = self.points[corner_keys[3]]

                grid[grid_name] = [
                    (p1[0] + offset, p1[1] + offset, z_val, r_val),
                    (p2[0] + offset, p2[1] - offset, z_val, r_val),
                    (p3[0] - offset, p3[1] + offset, z_val, r_val),
                    (p4[0] - offset, p4[1] - offset, z_val, r_val),
                ]

                grid[grid_name + "I"] = [
                    (p1[0] + offset, p1[1] + offset, z_val + 20, r_val),
                    (p2[0] + offset, p2[1] - offset, z_val + 20, r_val),
                    (p3[0] - offset, p3[1] + offset, z_val + 20, r_val),
                    (p4[0] - offset, p4[1] - offset, z_val + 20, r_val),
                ]
            except KeyError as e:
                print(f"Missing point {e} for grid {grid_name}, skipping.")
                continue

        self.grid = grid
        print("Grid coordinates generated successfully.")

    def move_to_point(self, key, delay=0):
        if key.lower() == "home":
            print("Moving to home position.")
            self.device.home()
            time.sleep(delay)
            return

        if key not in self.points:
            print(f"Warning: Point '{key}' not found!")
            return

        x, y, z, r = self.points[key]
        print(f"Moving to {key}: x={x}, y={y}, z={z}, r={r}")
        self.device.move_to(mode=int(MODE_PTP.MOVJ_XYZ), x=x, y=y, z=z, r=r)
        time.sleep(delay)
    
    def move_to_intermediate(self):
        x = self.intermediate[0]
        y = self.intermediate[1]
        z = self.intermediate[2]
        r = self.intermediate[3]
        print(f"Moving to intermdiate: x={x}, y={y}, z={z}, r={r}")
        self.device.move_to(mode=int(MODE_PTP.MOVJ_XYZ), x=x, y=y, z=z, r=r)
        time.sleep(7) # as moving is not a synchronous process, pause the flow until it is done

    def draw_grid(self):
        sequence = [
            "home",
            "SI1", "S1", "S2", "SI2",
            "SI3", "S3", "S4", "SI4",
            "SI5", "S5", "S6", "SI6",
            "SI7", "S7", "S8", "SI8",
            "home"
        ]

        for key in sequence:
            self.move_to_point(key)
        time.sleep(30) # as drawing is not a synchronous process, pause the flow until it is done

        print("Grid drawing completed successfully!")
    
    def draw_x(self, row, col, delay=0):
        grid_name = "G" + str(row) + str(col)
        grid_i_name = grid_name + "I"
        if grid_name not in self.grid or grid_i_name not in self.grid:
            print(f"Either '{grid_name}' or '{grid_i_name}' not found in grid data.")
            return

        grid = self.grid[grid_name]
        grid_i = self.grid[grid_i_name]

        print(f"Starting to draw X in {grid_name}.")
        motion_sequence = [
            "home",
            (grid_i[0], f"{grid_i_name}[0]"),
            (grid[0], f"{grid_name}[0]"),
            (grid[3], f"{grid_name}[3]"),
            (grid_i[3], f"{grid_i_name}[3]"),
            (grid_i[1], f"{grid_i_name}[1]"),
            (grid[1], f"{grid_name}[1]"),
            (grid[2], f"{grid_name}[2]"),
            (grid_i[2], f"{grid_i_name}[2]"),
            "home"
        ]

        for step in motion_sequence:
            if step == "home":
                print("Moving to home.")
                self.device.home()
                time.sleep(delay)
            else:
                (x, y, z, r), name = step
                # print(f"Moving to {name}: x={x:.2f}, y={y:.2f}, z={z:.2f}, r={r:.2f}")
                self.device.move_to(mode=int(MODE_PTP.MOVL_XYZ), x=x, y=y, z=z, r=r)
                time.sleep(delay)

        time.sleep(5) # as drawing is not a synchronous process, pause the flow until it is done
    
    def calculate_center(self, tuple_list):
        avg_tuple = tuple(
            sum(values) / len(values)
            for values in zip(*tuple_list)
        )
        return avg_tuple

    def draw_o(self, row, col, angle_step=25):
        radius = self.radius
        grid_name = "G" + str(row) + str(col)
        grid = self.grid[grid_name]
        center = self.calculate_center(grid)
        x_center = center[0]
        y_center = center[1]
        z = center[2]
        r = center[3]
        start_x = x_center + radius
        start_y = y_center

        self.device.move_to(mode=int(MODE_PTP.MOVL_XYZ), x=start_x, y=start_y, z=z+20, r=r)
        self.device.move_to(mode=int(MODE_PTP.MOVL_XYZ), x=start_x, y=start_y, z=z, r=r)

        for angle in range(0, 375, angle_step):
            rad = math.radians(angle)
            x = x_center + radius * math.cos(rad)
            y = y_center + radius * math.sin(rad)
            self.device.move_to(mode=int(MODE_PTP.MOVL_XYZ), x=x, y=y, z=z, r=r)
        self.device.home()
        time.sleep(5) # as drawing is not a synchronous process, pause the flow until it is done
    
    def disconnect(self):
        self.device.close()


if __name__ == "__main__":
    dobot = DobotGrid(port="/dev/ttyACM0")
    dobot.generate_points()
    dobot.generate_grid()
    dobot.draw_grid()
    dobot.draw_x(1,1)
    dobot.draw_o(2,2)
    dobot.draw_x(3,3)
    dobot.draw_o(3,1)
    dobot.disconnect()
