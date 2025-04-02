import tkinter as tk
import pyautogui
import time
import mouse
import keyboard
import mortar_tools.calculator as calc

class main():
    def __init__(self):
        self.title = "Mortar Distance Measurement Tool"
        self.geometry = "300x150"
        self.start_hotkey = "alt+q"
        self.point_hotkey = "alt+left"

    
    def create_static_window(self):
        window = tk.Tk()
        window.overrideredirect(True)
        window.geometry("+10+10")
        window.attributes("-topmost", True)
        label = tk.Label(window, font=("Helvetica", 14), bg="yellow", padx=10, pady=5)
        label.pack()
        return window, label

    def get_point(self):
        pos = None

        def on_click(event):
            nonlocal pos
            if isinstance(event, mouse.ButtonEvent) and event.event_type == 'down' and event.button == 'left' and keyboard.is_pressed(self.point_hotkey.split('+')[0]):
                pos = pyautogui.position()
                mouse.unhook(on_click)

        mouse.hook(on_click)

        # **等待用户点击**
        while pos is None:
            time.sleep(0.1)  # 防止 CPU 过载

        return pos
    
    def start_measurement(self):
        window, label = self.create_static_window()
        
        calculator = calc.calculator()

        # get point1 and point2 for scale factor
        label.config(text=f"Set 100 meters: First point")
        window.update()
        point1 = self.get_point()

        label.config(text=f"Set 100 meters: Second point")
        window.update()
        point2 = self.get_point()

        # calculate scale factor
        calculator.set_scale_factor(point1, point2)

        # get point1 and point2 for distance
        label.config(text=f"Measurement: First point")
        window.update()
        point1 = self.get_point()

        label.config(text=f"Measurement: Second point")
        window.update()
        point2 = self.get_point()

        # calculate horizontal distance
        calculator.get_horizontal_distance(point1, point2)
        
        label.config(text=f"MAX Distance: {calculator.horizontal_distance:.2f} m")
        window.update()
        # time.sleep(1)

        # get elevation angle point
        label.config(text=f"Elevation angle: Only one point")
        point = self.get_point()
        window.update()

        # calculate elevation angle
        label.config(text=f"Evelation angle: {calculator.get_evelation_angle(point):.2f} degrees")
        window.update()

        # calculate final distance
        label.config(text=f"Distance: {calculator.solve(calculator.evelation_angle, calculator.horizontal_distance):.2f} m")
        window.update()

        time.sleep(3)

        window.destroy()

    def main(self):
        # register hotkeys
        keyboard.add_hotkey(self.start_hotkey, self.start_measurement)
        keyboard.add_hotkey(self.point_hotkey, self.get_point)

        # create UI
        root = tk.Tk()
        root.title(self.title)
        root.geometry(self.geometry)
        root.attributes("-topmost", True)

        # text
        info_text = (
            "Control:\n"
            "Alt + Q: Start measurement\n"
            "Alt + Left: Set point\n\n"
        )

        message_label = tk.Label(root, text=info_text, font=("Console", 12), justify="left")
        message_label.pack(pady=20)

        root.mainloop()

if __name__ == "__main__":
    app = main()
    app.main()