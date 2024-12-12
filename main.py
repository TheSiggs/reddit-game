import pygame
import io
import unicodedata
import requests
import sys
import random
import math
import time
from google.cloud import texttospeech
from google.oauth2 import service_account

ENV = "prod"

# Initialize pygame
pygame.init()

# Set dimensions for a 9:16 aspect ratio canvas
canvas_width = 405
canvas_height = 720

# Create the screen directly with canvas dimensions
screen = pygame.display.set_mode((canvas_width, canvas_height))
pygame.display.set_caption("Bouncing Balls")
clock = pygame.time.Clock()

pygame.mixer.music.load("background.mp3")  # Replace with your music file path
pygame.mixer.music.set_volume(0.1)  # Set volume (0.0 to 1.0)
pygame.mixer.music.play(loops=-1)  # Play indefinitely (-1 for infinite loop)

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
    interval = 10  # Interval in seconds

font = pygame.font.Font(None, 36)  # You can replace None with a font path


def split_text_into_chunks(text, max_bytes=5000):
    """Split text into chunks of up to max_bytes."""
    chunks = []
    current_chunk = ""
    for word in text.split():
        # Check if adding the next word exceeds the byte limit
        if len(current_chunk.encode("utf-8")) + len(word.encode("utf-8")) + 1 > max_bytes:
            chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            current_chunk += " " + word
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def synthesize_chunks_to_audio_file(text, output_file):
    """Generate audio for long text by chunking and concatenating results."""
    chunks = split_text_into_chunks(text)
    print(f"Text split into {len(chunks)} chunks.")

    # Create an in-memory buffer to concatenate the audio
    credentials = service_account.Credentials.from_service_account_file("./google-tts-credentials.json")
    client = texttospeech.TextToSpeechClient(credentials=credentials)
    audio_data = io.BytesIO()

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i + 1}/{len(chunks)}...")

        # Set the text input
        input_text = texttospeech.SynthesisInput(text=chunk)

        # Set the voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Set the audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )

        # Append the audio content to the buffer
        audio_data.write(response.audio_content)

    # Write the concatenated audio to a file
    with open(output_file, "wb") as out:
        out.write(audio_data.getvalue())
        print(f"Audio content written to {output_file}")


def synthesize_speech(text):
    output_file = "tts_audio.mp3"
    synthesize_chunks_to_audio_file(text, output_file)
    return output_file, text.split()


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
    return [random.randint(2, 255), random.randint(2, 255), random.randint(2, 255)]


def get_segments():
    return random.randint(5, 20)


def shape_name(sides: int):
    shapes = {
        '5': "Pentagon",
        '6': "Hexagon",
        '7': "Heptagon",
        '8': "Octagon",
        '9': "Nonnagon or Enneagon",
        '10': "Decagon",
        '11': "Hendecagon or Undecagon",
        '12': "Dodecagon",
        '13': "Tridecagon or Triskaidecagon",
        '14': "Tetradecagon",
        '15': "Pentadecagon",
        '16': "Hexadecagon",
        '17': "Heptadecagon",
        '18': "Octadecagon",
        '19': "Enneadecagon or Nonadecagon",
        '20': "Icosagon",
        '21': "Icosikaihenagon",
        '22': "Icosikaidigon",
        '23': "Icosikaitrigon",
        '24': "Icosikaitetragon",
        '25': "Icosikaipentagon",
        '26': "Icosikaihexagon",
        '27': "Icosikaiheptagon",
        '28': "Icosikaioctagon",
        '29': "Icosikaienneagon",
        '30': "Triacontagon",
    }
    return shapes[f'{sides}']


def get_content(subreddit):
    for i in range(100):
        response = requests.get(subreddit['link'])
        if response.status_code == 200:
            posts = response.json()['data']['children'][:subreddit['posts']]
            content = []
            showTitle = subreddit['showTitle']
            showBody = subreddit['showBody']
            postsNo = subreddit['posts']
            title = unicodedata.normalize('NFC', posts[0]['data']['title']).encode('ascii', 'ignore').decode(
                'ascii')
            if postsNo > 1:
                for post in posts:
                    if showTitle:
                        text = unicodedata.normalize('NFC', post['data']['title']).encode('ascii', 'ignore').decode(
                            'ascii')
                        content.append(text)
                    if showBody:
                        bodyText = post['data']['selftext']
                        bodyText = unicodedata.normalize('NFC', bodyText).encode('ascii', 'ignore').decode('ascii')
                        words = bodyText.split('. ')
                        for chunk in words:
                            content.append(chunk + '. ')
            else:
                post = posts[0]
                if showTitle:
                    text = unicodedata.normalize('NFC', post['data']['title']).encode('ascii', 'ignore').decode(
                        'ascii')
                    content.append(text + '.')
                if showBody:
                    bodyText = post['data']['selftext']
                    bodyText = unicodedata.normalize('NFC', bodyText).encode('ascii', 'ignore').decode('ascii')
                    bodyText = bodyText.replace('\n\r', '', -1)
                    bodyText = bodyText.replace('\n', ' ', -1)
                    bodyText = bodyText.replace('\r', '', -1)
                    bodyText = bodyText.replace('."', '.". ', -1)
                    bodyText = bodyText.replace('?"', '?". ', -1)
                    words = bodyText.split('. ')
                    for chunk in words:
                        content.append(chunk + '. ')
            return content, title
        elif response.status_code == 429:
            print(f"Too many requests. Retrying in {2} seconds...")
            time.sleep(2)
        else:
            print("Failed to make request after 100 attempts.")


def write_text_to_file(text):
    with open("tts_audio.txt", 'w') as f:
        f.write(text)


def read_text_from_file():
    with open("tts_audio.txt", 'r') as f:
        content = f.read()
    return content


num_segments = get_segments()
segment_colors = [random_color() for _ in range(num_segments)]

# Prints Text
text = shape_name(num_segments)
text_surface = font.render(text, True, (255, 255, 255))
text_rect = text_surface.get_rect(center=(canvas_width // 2, text_surface.get_height() // 2))

# TTS
subreddit = {
    "name": "Am I The Asshole",
    "subreddit": "r/AmItheAsshole",
    "link": "https://www.reddit.com/r/AmItheAsshole/top/.json?limit=100",
    "posts": 100,
    "showTitle": True,
    "showBody": True,
    "addNameToTitle": False,
}

content, title = get_content(subreddit)
text_to_speak = "".join(content)
audio_data, subtitles = synthesize_speech(text_to_speak)
tts = pygame.mixer.Sound(audio_data)
tts.set_volume(0.5)
tts.play(loops=-1)

# Main loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get the current time
    current_time = time.time()

    # New Shape
    if current_time - last_time >= interval:
        num_segments = get_segments()
        segment_colors = [random_color() for _ in range(num_segments)]

        # Prints Text
        text = shape_name(num_segments)
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

pygame.mixer.music.stop()  # Stop the music when exiting
