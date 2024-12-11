import pygame
import json
import sys
import random
import math
import time


ENV = "prod"

# Initialize pygame
pygame.init()

# Set dimensions for a 9:16 aspect ratio canvas
canvas_width = 405
canvas_height = 720

# Create the screen directly with canvas dimensions
screen = pygame.display.set_mode((canvas_width, canvas_height))
pygame.display.set_caption("Bouncing Music")

# Ball settings
ball_radius = 20
ball_color = (255, 255, 255)  # White color for the ball
ball_x = canvas_width // 2  # Center X on the canvas
ball_y = canvas_height // 2  # Start in the middle of the canvas
ball_speed_x = 2             # Horizontal speed
ball_speed_y = 0             # Initial vertical speed
gravity = 0.1                # Gravity to increase speed over time
bounce_factor = -0.9         # Bounce factor for the ball's bounce off boundaries
min_bounce_speed = 2.0       # Threshold for triggering a big bounce
big_bounce_speed = -10.0     # Speed for the big bounce

# Ring settings
ring_radius = 200            # Radius for the ring boundary
inner_radius = 190           # Inner radius to keep it circular

last_color = (0, 0, 0)
rotation_angle = 0  # Rotation angle for the segments
rotation_speed = 0.5  # Speed of rotation, adjust for faster/slower rotation

last_time = time.time()  # Record the starting time
if ENV == "test":
    interval = 1  # Interval in seconds
else:
    interval = 60  # Interval in seconds

font = pygame.font.Font(None, 36)  # You can replace None with a font path


# Function to draw a filled segmented circle with rotation
def draw_rotating_segmented_circle(surface, center, outer_radius, inner_radius, num_segments, colors, rotation_angle):
    angle_per_segment = 360 / num_segments
    for i in range(num_segments):
        # Calculate start and end angles for the segment, adjusted by rotation
        start_angle = math.radians(i * angle_per_segment + rotation_angle)
        end_angle = math.radians((i + 1) * angle_per_segment + rotation_angle)

        # Calculate the points for the segment as a quadrilateral
        points = [
            (center[0] + inner_radius * math.cos(start_angle), center[1] + inner_radius * math.sin(start_angle)),
            (center[0] + outer_radius * math.cos(start_angle), center[1] + outer_radius * math.sin(start_angle)),
            (center[0] + outer_radius * math.cos(end_angle), center[1] + outer_radius * math.sin(end_angle)),
            (center[0] + inner_radius * math.cos(end_angle), center[1] + inner_radius * math.sin(end_angle))
        ]

        # Draw the filled polygon segment
        pygame.draw.polygon(surface, colors[i], points)


def random_color():
    return [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]


def load_themes():
    with open('themes.json', 'r') as file:
        themes = json.load(file)

    return themes


def new_theme(themes):
    if ENV == "test":
        for element in themes:
            yield element
    else:
        while True:  # Infinite generator
            yield random.choice(themes)


# initial startup
themes = load_themes()
theme_generator = new_theme(list(themes.keys()))

theme = next(theme_generator)
current_theme = theme
theme = themes[theme]
segment_sounds = theme["sounds"]
segment_colors = theme["color_palette"]
color_palette = theme["color_palette"]
num_segments = len(theme["sounds"])

text = current_theme.split("_")[0]
text_surface = font.render(text, True, (255, 255, 255))
text_rect = text_surface.get_rect(center=(canvas_width // 2, text_surface.get_height() // 2))

# Main loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get the current time
    current_time = time.time()

    if current_time - last_time >= interval:
        theme = next(theme_generator)
        current_theme = theme
        print(f"switching to theme {theme}")
        theme = themes[theme]
        segment_sounds = theme["sounds"]
        segment_colors = theme["color_palette"]
        color_palette = theme["color_palette"]
        num_segments = len(theme["sounds"])

        text = theme["name"]
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(canvas_width // 2, text_surface.get_height() // 2))

        # Reset the timer
        last_time = current_time

    # Fill the screen with a black background
    screen.fill((0, 0, 0))

    screen.blit(text_surface, text_rect)

    # Update the rotation angle
    rotation_angle = (rotation_angle + rotation_speed) % 360

    # Draw the rotating segmented circle
    ring_center = (canvas_width // 2, canvas_height // 2)
    draw_rotating_segmented_circle(screen, ring_center, ring_radius, inner_radius, num_segments, segment_colors, rotation_angle)

    # Apply gravity to the ball's vertical speed
    ball_speed_y += gravity
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # Calculate distance from ball center to ring center
    distance_to_center = ((ball_x - ring_center[0]) ** 2 + (ball_y - ring_center[1]) ** 2) ** 0.5

    # Check if the ball hits the inner boundary of the ring
    if distance_to_center + ball_radius > inner_radius:
        # Calculate the angle of collision from the center of the ring to the ball
        dx = ball_x - ring_center[0]
        dy = ball_y - ring_center[1]
        collision_angle = (math.degrees(math.atan2(dy, dx)) - rotation_angle + 360) % 360  # Adjust for rotation

        # Determine which segment was hit
        segment_index = int(collision_angle // (360 / num_segments))
        last_color = random_color()
        segment_colors[segment_index] = last_color

        # Reflect the ball's velocity based on the angle of collision
        direction = pygame.math.Vector2(ball_speed_x, ball_speed_y).reflect(pygame.math.Vector2(dx, dy).normalize())
        ball_speed_x, ball_speed_y = direction.x * abs(bounce_factor), direction.y * abs(bounce_factor)

        # Position the ball right at the edge of the ring to prevent sticking
        ball_x = ring_center[0] + (inner_radius - ball_radius) * (dx / distance_to_center)
        ball_y = ring_center[1] + (inner_radius - ball_radius) * (dy / distance_to_center)

        # If the bounce speed is too low, apply a big bounce
        if abs(ball_speed_y) < min_bounce_speed:
            ball_speed_y = big_bounce_speed

    # Draw the ball
    pygame.draw.circle(screen, ball_color, (int(ball_x), int(ball_y)), ball_radius)

    # Update the display
    pygame.display.flip()

    # Add a small delay to slow down the loop
    if ENV != "test":
        pygame.time.delay(10)
