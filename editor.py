import pygame
import sys

# Grid dimensions (must match main.py)
COLS = 80
ROWS = 65

# Editor modes
MODE_OBSTACLE = "obstacle"
MODE_START = "start"
MODE_END = "end"

class Cell:
    def __init__(self, i, j):
        # Grid coordinates (x, y)
        self.x = i
        self.y = j
        self.obstacle = False

    def toggle(self):
        """Toggle obstacle state"""
        self.obstacle = not self.obstacle

    def show(self, screen, w, h, is_start=False, is_end=False):
        # Create surface with transparency
        cell_surface = pygame.Surface((w-1, h-1), pygame.SRCALPHA)

        if is_start:
            # Start point in cyan
            pygame.draw.rect(cell_surface, (0, 255, 255, 220), (0, 0, w-1, h-1), 0)
        elif is_end:
            # End point in magenta
            pygame.draw.rect(cell_surface, (255, 0, 255, 220), (0, 0, w-1, h-1), 0)
        elif self.obstacle:
            # Obstacles with less transparency (red)
            pygame.draw.rect(cell_surface, (255, 0, 0, 180), (0, 0, w-1, h-1), 0)
        else:
            # Just grid lines for non-obstacles
            pygame.draw.rect(cell_surface, (255, 255, 255, 30), (0, 0, w-1, h-1), 1)

        # Draw surface on screen
        screen.blit(cell_surface, (self.x * w, self.y * h))


def load_obstacles_from_file(filename):
    """Load obstacles from file"""
    loaded_obstacles = set()
    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    if ',' in line:
                        parts = line.split(',')
                    else:
                        parts = line.split()

                    if len(parts) >= 2:
                        try:
                            x = int(parts[0])
                            y = int(parts[1])
                            loaded_obstacles.add((x, y))
                        except ValueError:
                            print(f"Error converting coordinates: {line}")
        print(f"Loaded {len(loaded_obstacles)} obstacles from {filename}")
        return loaded_obstacles
    except FileNotFoundError:
        print(f"File {filename} not found. Starting with empty obstacles.")
        return set()


def save_obstacles_to_file(filename, obstacles_set):
    """Save obstacles to file"""
    with open(filename, 'w') as file:
        for x, y in sorted(obstacles_set):
            file.write(f"{x},{y}\n")
    print(f"Saved {len(obstacles_set)} obstacles to {filename}")


def load_points_from_file(filename):
    """Load start and end points from file"""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                start_parts = lines[0].strip().split(',')
                end_parts = lines[1].strip().split(',')

                start = (int(start_parts[0]), int(start_parts[1]))
                end = (int(end_parts[0]), int(end_parts[1]))

                print(f"Loaded start {start} and end {end} from {filename}")
                return start, end
    except (FileNotFoundError, ValueError, IndexError) as e:
        print(f"Error loading points from {filename}: {e}")

    # Default values
    return (64, 15), (6, 51)


def save_points_to_file(filename, start, end):
    """Save start and end points to file"""
    with open(filename, 'w') as file:
        file.write(f"{start[0]},{start[1]}\n")
        file.write(f"{end[0]},{end[1]}\n")
    print(f"Saved start {start} and end {end} to {filename}")


def setup(obstacle_file, points_file):
    """Setup grid and load data"""
    grid = []

    # Create grid
    for i in range(COLS):
        row = []
        for j in range(ROWS):
            cell = Cell(i, j)
            row.append(cell)
        grid.append(row)

    # Load obstacles from file
    obstacles = load_obstacles_from_file(obstacle_file)
    for x, y in obstacles:
        if 0 <= x < COLS and 0 <= y < ROWS:
            grid[x][y].obstacle = True

    # Load start and end points
    start, end = load_points_from_file(points_file)

    return grid, obstacles, start, end


def get_cell_from_mouse(mouse_pos, cell_width, cell_height):
    """Convert mouse position to grid coordinates"""
    col = int(mouse_pos[0] / cell_width)
    row = int(mouse_pos[1] / cell_height)

    # Ensure within bounds
    col = max(0, min(col, COLS-1))
    row = max(0, min(row, ROWS-1))

    return col, row


def main():
    """Main editor function"""
    # File paths
    obstacle_file = "data/obstacles.txt"
    points_file = "data/points.txt"

    # Initialize pygame
    pygame.init()

    # Screen dimensions
    screen_width = 1280
    screen_height = 1040

    # Create screen
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("A* Pathfinding Editor")

    # Load background image
    try:
        bg_image = pygame.image.load('data/farm.png')
        bg_image = pygame.transform.scale(bg_image, (screen_width, screen_height))
    except pygame.error:
        print("Error loading background image. Make sure 'data/farm.png' exists.")
        bg_image = None

    # Calculate cell size
    cell_width = screen_width / COLS
    cell_height = screen_height / ROWS

    # Setup grid and load data
    grid, obstacles, start_point, end_point = setup(obstacle_file, points_file)

    # Editor mode
    current_mode = MODE_OBSTACLE
    drawing = False
    erasing = False

    # Main loop
    running = True
    clock = pygame.time.Clock()

    # Font for instructions
    font = pygame.font.SysFont('Arial', 16)
    instructions = [
        f"Mode: {current_mode.upper()} (1: Obstacles, 2: Start, 3: End)",
        "Left Click: Add/Set | Right Click: Remove",
        "S: Save | L: Load | C: Clear All (hold Shift)",
        "X: Toggle Coordinates | ESC: Exit"
    ]

    # Display options
    show_coordinates = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Keyboard events
            elif event.type == pygame.KEYDOWN:
                # Save data
                if event.key == pygame.K_s:
                    save_obstacles_to_file(obstacle_file, obstacles)
                    save_points_to_file(points_file, start_point, end_point)

                # Load data
                elif event.key == pygame.K_l:
                    obstacles = load_obstacles_from_file(obstacle_file)
                    start_point, end_point = load_points_from_file(points_file)
                    # Update grid
                    for i in range(COLS):
                        for j in range(ROWS):
                            grid[i][j].obstacle = (i, j) in obstacles

                # Clear obstacles
                elif event.key == pygame.K_c:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        obstacles.clear()
                        for i in range(COLS):
                            for j in range(ROWS):
                                grid[i][j].obstacle = False
                        print("All obstacles cleared")

                # Toggle coordinates display
                elif event.key == pygame.K_x:
                    show_coordinates = not show_coordinates
                    print(f"Coordinate display: {'Enabled' if show_coordinates else 'Disabled'}")

                # Switch modes
                elif event.key == pygame.K_1:
                    current_mode = MODE_OBSTACLE
                    instructions[0] = f"Mode: {current_mode.upper()} (1: Obstacles, 2: Start, 3: End)"
                    print(f"Switched to {current_mode.upper()} mode")

                elif event.key == pygame.K_2:
                    current_mode = MODE_START
                    instructions[0] = f"Mode: {current_mode.upper()} (1: Obstacles, 2: Start, 3: End)"
                    print(f"Switched to {current_mode.upper()} mode")

                elif event.key == pygame.K_3:
                    current_mode = MODE_END
                    instructions[0] = f"Mode: {current_mode.upper()} (1: Obstacles, 2: Start, 3: End)"
                    print(f"Switched to {current_mode.upper()} mode")

                # Exit
                elif event.key == pygame.K_ESCAPE:
                    running = False

            # Mouse button down
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                col, row = get_cell_from_mouse(mouse_pos, cell_width, cell_height)

                if event.button == 1:  # Left click
                    if current_mode == MODE_OBSTACLE:
                        drawing = True
                        erasing = False
                        if not grid[col][row].obstacle:
                            grid[col][row].toggle()
                            obstacles.add((col, row))
                            print(f"Added obstacle at ({col},{row})")
                    elif current_mode == MODE_START:
                        # Remove from obstacles if needed
                        if (col, row) in obstacles:
                            obstacles.remove((col, row))
                            grid[col][row].obstacle = False
                        start_point = (col, row)
                        print(f"Set start point to ({col},{row})")
                    elif current_mode == MODE_END:
                        # Remove from obstacles if needed
                        if (col, row) in obstacles:
                            obstacles.remove((col, row))
                            grid[col][row].obstacle = False
                        end_point = (col, row)
                        print(f"Set end point to ({col},{row})")

                elif event.button == 3:  # Right click
                    if current_mode == MODE_OBSTACLE:
                        erasing = True
                        drawing = False
                        if grid[col][row].obstacle:
                            grid[col][row].toggle()
                            obstacles.discard((col, row))
                            print(f"Removed obstacle at ({col},{row})")

            # Mouse motion (for drawing/erasing obstacles)
            elif event.type == pygame.MOUSEMOTION:
                if current_mode == MODE_OBSTACLE and (drawing or erasing):
                    mouse_pos = pygame.mouse.get_pos()
                    col, row = get_cell_from_mouse(mouse_pos, cell_width, cell_height)

                    if 0 <= col < COLS and 0 <= row < ROWS:
                        if drawing and not grid[col][row].obstacle:
                            grid[col][row].toggle()
                            obstacles.add((col, row))
                        elif erasing and grid[col][row].obstacle:
                            grid[col][row].toggle()
                            obstacles.discard((col, row))

            # Mouse button up
            elif event.type == pygame.MOUSEBUTTONUP:
                drawing = False
                erasing = False

        # Draw background
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Draw grid
        for i in range(COLS):
            for j in range(ROWS):
                is_start = (i, j) == start_point
                is_end = (i, j) == end_point
                grid[i][j].show(screen, cell_width, cell_height, is_start, is_end)

        # Show coordinates under mouse if enabled
        if show_coordinates:
            mouse_pos = pygame.mouse.get_pos()
            col, row = get_cell_from_mouse(mouse_pos, cell_width, cell_height)
            coord_text = font.render(f"({col},{row})", True, (255, 255, 0))
            # Add background for readability
            bg_rect = coord_text.get_rect()
            bg_rect.topleft = (mouse_pos[0] + 10, mouse_pos[1] + 10)
            bg_surface = pygame.Surface((bg_rect.width + 10, bg_rect.height + 5))
            bg_surface.set_alpha(200)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, (mouse_pos[0] + 8, mouse_pos[1] + 8))
            screen.blit(coord_text, (mouse_pos[0] + 10, mouse_pos[1] + 10))

        # Draw instructions
        for i, text in enumerate(instructions):
            text_surface = font.render(text, True, (255, 255, 255))
            # Add background for readability
            bg_rect = text_surface.get_rect()
            bg_rect.topleft = (10, 10 + i*22)
            bg_surface = pygame.Surface((bg_rect.width + 10, bg_rect.height + 5))
            bg_surface.set_alpha(180)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, (5, 8 + i*22))
            screen.blit(text_surface, (10, 10 + i*22))

        # Display obstacle count and points
        info_y = screen_height - 70
        info_texts = [
            f"Obstacles: {len(obstacles)}",
            f"Start: {start_point}",
            f"End: {end_point}"
        ]
        for i, text in enumerate(info_texts):
            text_surface = font.render(text, True, (255, 255, 255))
            bg_rect = text_surface.get_rect()
            bg_rect.topleft = (10, info_y + i*22)
            bg_surface = pygame.Surface((bg_rect.width + 10, bg_rect.height + 5))
            bg_surface.set_alpha(180)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, (5, info_y - 2 + i*22))
            screen.blit(text_surface, (10, info_y + i*22))

        pygame.display.flip()
        clock.tick(60)

    # Save before exiting
    print("Saving before exit...")
    save_obstacles_to_file(obstacle_file, obstacles)
    save_points_to_file(points_file, start_point, end_point)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
