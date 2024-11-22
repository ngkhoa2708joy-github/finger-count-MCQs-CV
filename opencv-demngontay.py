import cv2
import time
import os
import hand as htm
from questions import questions
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from progessBar import ProgressBar

# Initialize video capture
cap = cv2.VideoCapture(0)

# Set desired window dimensions
window_width = 980
window_height = 740

background_image = cv2.imread('background.jpg')  # Replace 'background.jpg' with your image path
background_image_question = cv2.imread('background2.jpg')  # Replace 'background.jpg' with your image path
background_image_question = cv2.resize(background_image_question, (520, window_height))

# Load finger images
FolderPath = "Fingers"
lst = os.listdir(FolderPath)
print(lst)
lst_2 = []

for i in lst:
    image = cv2.imread(f"{FolderPath}/{i}")  # Load images from the folder
    lst_2.append(image)

detector = htm.handDetector(detectionCon=0.55)

ptime = 0
fingerTop_id = [4, 8, 12, 16, 20]  # Finger tip IDs

current_question = 0
total_questions = len(questions)
score = 0  # Starting score
quiz_ended = False  # Flag to check if the quiz has ended
quiz_start = False
feedback_message = ""
answer_checked = False  # Initialize answer_checked flag

#Timing countdown
initial_question_time = 8  # Time allowed to answer each question
countdown_time = initial_question_time  # Initialize the countdown time
progress_bar = ProgressBar(440, 25, 30, 570, 8)  # (width, height, x, y, time)

def wrap_text(text, font, max_width):
    """Wraps text to fit within the specified width."""
    words = text.split(' ')
    wrapped_lines = []
    current_line = ""

    for word in words:
        # Check the width of the current line with the new word added
        test_line = current_line + word + " "
        bbox = font.getbbox(test_line)
        test_line_width = bbox[2] - bbox[0]  # Width of the text

        if test_line_width <= max_width:
            current_line = test_line
        else:
            wrapped_lines.append(current_line.strip())
            current_line = word + " "  # Start a new line with the current word

    if current_line:
        wrapped_lines.append(current_line.strip())  # Don't forget the last line

    return wrapped_lines


def display_question(frame, question_data, score, selected_answer):
    """Displays the question, choices, and current score with support for Vietnamese characters."""
    frame[:] = background_image_question

    # Convert OpenCV frame to PIL format
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # Load font that supports Vietnamese
    try:
        font = ImageFont.truetype("./GenBasB.ttf", 32)  # Ensure this path is correct
    except Exception as e:
        print(f"Error loading font: {e}")
        # Fallback to a default font
        font = ImageFont.load_default()
        print("Fallback to default font.")

    # Wrap the question text
    wrapped_question = wrap_text(question_data["question"], font, 480)  # Giữ nguyên max width

    # Display each wrapped line of the question
    for idx, line in enumerate(wrapped_question):
        draw.text((40, 70 + (idx * 40)), line, font=font, fill=(255, 255, 255))

    # Display the choices
    for idx, choice in enumerate(question_data["choices"]):
        color = (100, 100, 200) if selected_answer == idx + 1 else (200, 200, 200)  # Hover color
        draw.rectangle(
            [20, 150 + ((len(wrapped_question) + idx) * 40), 450, 190 + ((len(wrapped_question) + idx) * 40)],
            fill=color)
        draw.text((40, 150 + ((len(wrapped_question) + idx) * 40)), choice, font=font, fill=(255, 255, 255))

    # Display the score
    draw.text((30, 20), f"SCORE: {score}", font=font, fill=(255, 255, 0))

    # Convert back to OpenCV format
    frame[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)  # Update the frame directly

    return frame


feedback_start_time = None  # To track when to start showing feedback
feedback_display_time = 2   # Time to show feedback in seconds
def display_feedback(frame, message, score, feedback_position):
    """Displays feedback with slide-in animation."""
    cv2.putText(frame, message, (feedback_position, 680), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0) if "Correct" in message else (0, 0, 255), 3)
    cv2.putText(frame, f"Updated Score: {score}", (feedback_position, 650), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

# Add these variables at the top of your while loop
fade_value = 10  # To control the fade-in effect
fade_step = 100   # Change this value for speed of fade-in
feedback_position = 300  # Start position for feedback sliding in

def is_ok(lmlist):
    if len(lmlist) < 21:  # Check if the list has at least 21 landmarks
        return False

    three_finger_open = 0
    for i in range(1, 5):
        if lmlist[fingerTop_id[i]][2] < lmlist[fingerTop_id[i] - 2][2]:
            three_finger_open += 1

    result1 = lmlist[fingerTop_id[0]][2] - lmlist[fingerTop_id[1]][2]
    return result1 <= 40 and three_finger_open == 3

while True:
    ret, frame = cap.read()
    frame = cv2.resize(frame, (window_width, window_height))  # Resize frame
    frame = detector.findHands(frame)
    lmlist = detector.findPosition(frame, draw=False)
    selected_answer = 0
    count_finger_open = 0

    if len(lmlist) != 0:
        if is_ok(lmlist):
            cv2.putText(frame, "Gesture OK!", (400, 700), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        finger_open = []
        if lmlist[fingerTop_id[0]][1] >= lmlist[fingerTop_id[0] - 2][1]:
            finger_open.append(1)

        for i in range(1, 5):
            if lmlist[fingerTop_id[i]][2] < lmlist[fingerTop_id[i] - 2][2]:
                finger_open.append(1)
            else:
                finger_open.append(0)

        count_finger_open = finger_open.count(1)
        selected_answer = count_finger_open  # Select answer based on number of open fingers

    background_image = cv2.resize(background_image_question, (520, window_height))

    if not quiz_start:
        if is_ok(lmlist):
            quiz_start = True  # Start the quiz
            question_start_time = time.time()  # Reset timer for the first question
            fade_value = 255  # Start the fade value to make the text fully visible
        else:
            cv2.putText(background_image, "Welcome to the Quiz!", (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3)
            cv2.putText(background_image, "Please show OK to start!", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    elif not quiz_ended:
        if fade_value > 0:  # Gradually decrease fade value
            fade_value -= fade_step
        display_question(background_image, questions[current_question], score, selected_answer)

        elapsed_time = time.time() - question_start_time
        countdown_time = max(0, initial_question_time - int(elapsed_time))

        cv2.putText(background_image, f"Time left: {countdown_time}s", (40, 550), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (255, 0, 0), 3)

        # Update the progress bar based on elapsed time
        progress_bar.update(elapsed_time)

        # Draw the updated progress bar on the frame
        progress_bar.draw(background_image)

        if feedback_start_time is None:  # If feedback is not being displayed
            if elapsed_time >= 8 and not answer_checked:  # 8 seconds for answering
                if selected_answer in [1, 2, 3, 4]:
                    feedback_message = "Correct!" if selected_answer == questions[current_question][
                        "correct"] else "Wrong!"
                    if (selected_answer == questions[current_question]["correct"]):
                        score = score + 1
                    elif (score == 0 ):
                        score = 0  # Update score
                    else:
                        score = score -1

                # New Logic: Check if no fingers are shown
                if count_finger_open == 0:
                    feedback_message = "Wrong! No answer given."
                    if (score == 0):
                        score = 0
                    else:
                        score -= 1  # Deduct score for no answer

                feedback_start_time = time.time()  # Start the feedback timer
                answer_checked = True  # Set answer checked

        else:  # Feedback is currently being displayed
            elapsed_feedback_time = time.time() - feedback_start_time
            # Slide the feedback message in
            feedback_position = max(50, feedback_position - 10)  # Move position to the left
            display_feedback(background_image, feedback_message, score, feedback_position)

            if elapsed_feedback_time >= feedback_display_time:  # After 2 seconds
                # Move to the next question
                current_question = (current_question + 1) % total_questions
                question_start_time = time.time()  # Reset the timer for the next question
                feedback_start_time = None  # Reset for the next question
                answer_checked = False  # Reset for the next question
                feedback_position = 300  # Reset feedback position

                # Check if we have completed all questions
                if current_question == 0:  # End the quiz after completing all questions
                    quiz_ended = True

    # If the quiz is ended, display the final message and do nothing more
    if quiz_ended:
        final_message = f"Your Total Score: {score}"
        cv2.putText(background_image, "Quiz Finished!", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 0), 3)
        cv2.putText(background_image, final_message, (100, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.putText(background_image, "Press 'r' to Restart or 'q' to Quit", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    h, w, c = lst_2[count_finger_open - 1].shape
    frame[0:h, 0:w] = lst_2[count_finger_open - 1]
    # Show the frames
    ctime = time.time()
    fps = 1 / (ctime - ptime)
    ptime = ctime

    cv2.putText(frame, "Finger Detection App", (130, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    color = (0, 255, 0) if count_finger_open >= 1 else (0, 0, 255)
    cv2.rectangle(frame, (0, 800), (300, 648), color, -1)
    cv2.putText(frame, f"Open Fingers: {count_finger_open}", (8, 700), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
    cv2.putText(frame, f"FPS: {int(fps)}", (800, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Fingers Detection", frame)
    cv2.imshow("Quiz Screen", background_image)

    key = cv2.waitKey(1)
    if key == ord("q"):  # Press 'q' to exit
        print("Exiting the program...")
        break
    elif key == ord("r") and quiz_ended:  # Press 'r' to restart the quiz
        current_question = 0
        score = 10  # Reset score to initial value
        quiz_ended = False  # Reset quiz status
        quiz_start = False  # Reset quiz start to ask for OK gesture again

cap.release()
cv2.destroyAllWindows()
