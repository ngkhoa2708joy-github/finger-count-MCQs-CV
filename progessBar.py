# progressBar.py
import cv2

class ProgressBar():
    def __init__(self, max_width, height, x, y, initial_time):
        self.max_width = max_width
        self.height = height
        self.x = x
        self.y = y
        self.initial_time = initial_time
        self.remaining_time = initial_time

    def update(self, elapsed_time):
        # Update the remaining time
        self.remaining_time = max(0, self.initial_time - elapsed_time)

    def draw(self, frame):
        current_width = int((self.remaining_time / self.initial_time) * self.max_width)
        cv2.rectangle(frame, (self.x, self.y),
                      (self.x + current_width, self.y + self.height), (0, 255, 0), -1)
        # Draw the border
        cv2.rectangle(frame, (self.x, self.y),
                      (self.x + self.max_width, self.y + self.height), (255, 255, 255), 2)
