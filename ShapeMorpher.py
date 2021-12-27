from MorphingOptimizer import MorphingOptimizer
from tkinter import *
import numpy as np
import time


class ShapeMorpherWindow(Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Shape morpher")

        self._selected_data = {"x": 0, "y": 0, 'item': None}
        self.radius = 5
        self.n_points = {"src": 0, "dst": 0}

        self.rowconfigure([0, 1], weight=1, minsize=200)
        self.columnconfigure([0, 1], weight=1, minsize=200)

        self.columnconfigure(2, weight=0, minsize=200)

        self.setup_canvas()
        self.setup_panel()

    # Setup
    def setup_canvas(self):
        self.graph = Canvas(self, bd=2, cursor="plus", bg="#fbfbfb")
        self.graph.grid(row=0,
                        column=0,
                        padx=2,
                        pady=2,
                        rowspan=2,
                        columnspan=2,
                        sticky="nsew")

        self.graph.bind('<Button-1>', self.handle_canvas_click)
        self.graph.tag_bind("points_src", "<ButtonRelease-1>",
                            self.handle_drag_stop)
        self.graph.tag_bind("points_dst", "<ButtonRelease-1>",
                            self.handle_drag_stop)
        self.graph.bind("<B1-Motion>", self.handle_drag)

    def setup_panel(self):
        # Right panel for options
        self.frame_pannel = Frame(self, relief=RAISED, bg="#e1e1e1")
        self.frame_points_type = Frame(self.frame_pannel, bg="#e1e1e1")
        self.frame_edit_mode = Frame(self.frame_pannel, bg="#e1e1e1")
        self.frame_polygon = Frame(self.frame_pannel, bg="#e1e1e1")
        self.frame_edit_position = Frame(self.frame_pannel, bg="#e1e1e1")
        self.frame_resolution_sliders = Frame(self.frame_pannel, bg="#e1e1e1")

        # Selection of edit mode
        self.label_edit_mode = Label(self.frame_edit_mode, text="Edit mode:")
        self.label_edit_mode.pack()
        edit_mode = ['Add', 'Remove', 'Drag', 'Select']
        edit_mode_val = ["add", "remove", "drag", "select"]
        self.edit_mode = StringVar()
        self.edit_mode.set(edit_mode_val[0])

        self.radio_edit_buttons = [None] * 4
        for i in range(4):
            self.radio_edit_buttons[i] = Radiobutton(self.frame_edit_mode,
                                                     variable=self.edit_mode,
                                                     text=edit_mode[i],
                                                     value=edit_mode_val[i],
                                                     bg="#e1e1e1")
            self.radio_edit_buttons[i].pack(side='left', expand=1)
            self.radio_edit_buttons[i].bind(
                "<ButtonRelease-1>", lambda event: self.reset_selection())

        # Selection of points_type
        self.label_points_type = Label(self.frame_edit_mode,
                                       text="Curve mode:")
        self.label_points_type.pack()
        points_types = ['Source', 'Destination']
        points_type_val = ["src", "dst"]
        self.points_type = StringVar()
        self.points_type.set(points_type_val[0])

        self.radio_points_type_buttons = [None] * 2
        for i in range(2):
            self.radio_points_type_buttons[i] = Radiobutton(
                self.frame_points_type,
                variable=self.points_type,
                text=points_types[i],
                value=points_type_val[i],
                bg="#e1e1e1")
            self.radio_points_type_buttons[i].pack(side='left', expand=1)
            self.radio_points_type_buttons[i].bind(
                "<ButtonRelease-1>", lambda event: self.reset_selection())

        # Edit position of selected point widget
        self.label_pos_x = Label(self.frame_edit_position, text='x: ')
        self.label_pos_y = Label(self.frame_edit_position, text='y: ')
        self.pos_x = StringVar()
        self.pos_y = StringVar()
        self.entry_position_x = Entry(self.frame_edit_position,
                                      textvariable=self.pos_x)
        self.entry_position_y = Entry(self.frame_edit_position,
                                      textvariable=self.pos_y)
        self.label_pos_x.pack(side=LEFT)
        self.entry_position_x.pack(side=LEFT)
        self.label_pos_y.pack(side=LEFT)
        self.entry_position_y.pack(side=LEFT)

        self.entry_position_x.bind("<FocusOut>", self.update_pos)
        self.entry_position_x.bind("<KeyPress-Return>", self.update_pos)
        self.entry_position_x.bind("<KeyPress-KP_Enter>", self.update_pos)

        self.entry_position_y.bind("<FocusOut>", self.update_pos)
        self.entry_position_y.bind("<KeyPress-Return>", self.update_pos)
        self.entry_position_x.bind("<KeyPress-KP_Enter>", self.update_pos)

        # Slider for parameter update
        self.label_resolution = Label(self.frame_resolution_sliders,
                                      text="Resolution: ")
        self.slider_resolution = Scale(self.frame_resolution_sliders,
                                       from_=5,
                                       to=500,
                                       orient=HORIZONTAL,
                                       bg="#e1e1e1")
        self.slider_resolution.set(50)
        self.label_resolution.pack(side=LEFT)
        self.slider_resolution.pack(fill="x")

        # Frame pack
        self.frame_pannel.grid(row=0,
                               column=2,
                               padx=2,
                               pady=2,
                               rowspan=2,
                               sticky="nswe")
        self.frame_points_type.pack(fill="x")
        self.frame_edit_mode.pack(fill="x")
        self.frame_edit_position.pack(fill="x")
        self.frame_resolution_sliders.pack(fill="x")

        self.button_start = Button(self.frame_pannel, text="Start")
        self.button_start.pack(side=BOTTOM, fill="x")
        self.button_start.bind("<ButtonRelease-1>",
                               lambda event: self.start_interpolation())

        self.button_reset = Button(self.frame_pannel, text="Reset")
        self.button_reset.pack(side=BOTTOM, fill="x")
        self.button_reset.bind("<ButtonRelease-1>", lambda event: self.reset())

    # Drawing
    def get_points(self, ptype):
        points = []
        for item in self.graph.find_withtag(f"points_{ptype}"):
            coords = self.graph.coords(item)
            points.append([
                float(coords[0] + self.radius),
                float(coords[1] + self.radius)
            ])  # Ensure curve accuracy
        return points

    def create_point(self, x, y, color, tag):
        """Create a token at the given coordinate in the given color"""
        item = self.graph.create_oval(x - self.radius,
                                      y - self.radius,
                                      x + self.radius,
                                      y + self.radius,
                                      outline=color,
                                      fill=color,
                                      tags=tag)
        self.n_points[self.points_type.get()] += 1
        return item

    def draw_polygon(self, points, color, tag):
        for i in range(0, len(points) - 1):
            self.graph.create_line(points[i][0],
                                   points[i][1],
                                   points[i + 1][0],
                                   points[i + 1][1],
                                   fill=color,
                                   tags=tag)
        self.graph.create_line(points[-1][0],
                               points[-1][1],
                               points[0][0],
                               points[0][1],
                               fill=color,
                               tags=tag)

    def draw_control_polygon(self, ptype):
        self.graph.delete(f"polygon_{ptype}")

        color = "blue" if ptype == "src" else "red"
        self.draw_polygon(self.get_points(ptype),
                          color,
                          tag=f"polygon_{ptype}")

    def draw_breakline(self, points, color, tags):
        for i in range(0, points.shape[0] - 1):
            self.graph.create_line(points[i, 0],
                                   points[i, 1],
                                   points[i + 1, 0],
                                   points[i + 1, 1],
                                   fill=color,
                                   width=3,
                                   tags=tags)

    def animate(self, src_points, dst_points, T):
        for t in T:
            self.graph.delete("animation_point")
            self.graph.delete("animation_polygon")
            src_points = np.array(src_points)
            dst_points = np.array(dst_points)

            self.draw_polygon((1 - t) * src_points + t * dst_points,
                              color='green',
                              tag='animation_polygon')
            self.graph.update()

            time.sleep(len(T) / (T[-1] - T[0]) / 1000)
        self.graph.delete("animation_point")
        self.graph.delete("animation_polygon")

    def start_interpolation(self):
        if not (self.n_points["src"] > 2 and self.n_points["dst"] > 2):
            return
        self.graph.delete("matching")
        T = np.linspace(0, 1, self.slider_resolution.get())
        src_points = self.get_points("src")
        dst_points = self.get_points("dst")

        solver = MorphingOptimizer(src_points=src_points,
                                   dst_points=dst_points)
        solver.build()
        solver.solve()

        if solver.ns < solver.nd:
            for k in range(solver.nd - solver.ns):
                i = int(np.argmax(solver.s[k]))
                src_points.append(src_points[i])
        elif solver.ns > solver.nd:
            for k in range(solver.ns - solver.nd):
                j = int(np.argmax(solver.s[k]))
                dst_points.append(dst_points[j])

        self.animate(src_points, dst_points, T)

    # Event handling
    def find_closest_with_tag(self, x, y, radius, tag):
        distances = []
        for item in self.graph.find_withtag(tag):
            c = self.graph.coords(item)
            d = (x - c[0])**2 + (y - c[1])**2
            if d <= radius**2:
                distances.append((item, c, d))

        return min(distances,
                   default=(None, [0, 0], float("inf")),
                   key=lambda p: p[2])

    def reset_selection(self):
        if self._selected_data['item'] is not None:
            self.graph.itemconfig(self._selected_data['item'], fill='red')

        self._selected_data['item'] = None
        self._selected_data["x"] = 0
        self._selected_data["y"] = 0

    def handle_canvas_click(self, event):
        self.reset_selection()

        if self.edit_mode.get() == "add":
            item = self.create_point(event.x,
                                     event.y,
                                     "red",
                                     tag=f"points_{self.points_type.get()}")
            self.update_pos_entry(item)
            self.draw_control_polygon(self.points_type.get())

        elif self.edit_mode.get() == "remove":
            self._selected_data[
                'item'], coords, _ = self.find_closest_with_tag(
                    event.x, event.y, 3 * self.radius,
                    f"points_{self.points_type.get()}")
            if self._selected_data['item'] is not None:
                self.graph.delete(self._selected_data['item'])
                self.n_points[self.points_type.get()] -= 1

                self.draw_control_polygon(self.points_type.get())

        elif self.edit_mode.get() == "drag":
            self._selected_data[
                'item'], coords, _ = self.find_closest_with_tag(
                    event.x, event.y, 3 * self.radius,
                    f"points_{self.points_type.get()}")

            if self._selected_data['item'] is not None:
                self._selected_data["x"] = event.x
                self._selected_data["y"] = event.y
                self.graph.move(self._selected_data['item'],
                                event.x - coords[0] - self.radius,
                                event.y - coords[1] - self.radius)

        else:
            self._selected_data[
                'item'], coords, _ = self.find_closest_with_tag(
                    event.x, event.y, 3 * self.radius,
                    f"points_{self.points_type.get()}")
            if self._selected_data['item'] is not None:
                self.graph.itemconfig(self._selected_data['item'],
                                      fill='orange')  # Mark as selected
                self.update_pos_entry(self._selected_data['item'])

    def handle_drag_stop(self, event):
        """End drag of an object"""
        if self.edit_mode.get() != "drag":
            return
        self.reset_selection()

    def handle_drag(self, event):
        """Handle dragging of an object"""
        if self.edit_mode.get() != "drag" or self._selected_data[
                'item'] is None or f"points_{self.points_type.get()}" not in self.graph.gettags(
                    self._selected_data['item']):
            return

        # compute how much the mouse has moved
        delta_x = event.x - self._selected_data["x"]
        delta_y = event.y - self._selected_data["y"]
        # move the object the appropriate amount
        self.graph.move(self._selected_data['item'], delta_x, delta_y)
        # record the new position
        self._selected_data["x"] = event.x
        self._selected_data["y"] = event.y

        self.update_pos_entry(self._selected_data['item'])
        self.draw_control_polygon(self.points_type.get())

    def reset(self):
        self.graph.delete("all")

    def update_pos_entry(self, item):
        coords = self.graph.coords(item)
        self.entry_position_x.delete(0, END)
        self.entry_position_x.insert(0, int(coords[0]))
        self.entry_position_y.delete(0, END)
        self.entry_position_y.insert(0, int(coords[1]))

    def update_pos(self, event):
        if self.edit_mode.get(
        ) != "select" or self._selected_data['item'] is None:
            return

        coords = self.graph.coords(self._selected_data['item'])
        self.graph.move(self._selected_data['item'],
                        int(self.pos_x.get()) - coords[0],
                        int(self.pos_y.get()) - coords[1])

        self.draw_control_polygon(self.points_type.get())


if __name__ == "__main__":
    window = ShapeMorpherWindow()

    window.mainloop()
