import pygame
import heapq
import sys

# Grid dimensions
COLS = 80
ROWS = 65

class Cell:
    def __init__(self, i, j):
        # Grid coordinates (x, y)
        self.x = i
        self.y = j

        # A* values: f = g + h
        self.f = 0
        self.g = 0
        self.h = 0

        # Neighbors and parent (previous cell in path)
        self.neighbors = []
        self.parent = None

        self.obstacle = False

    def __lt__(self, other):
        # For heap comparison
        return self.f < other.f

    def show(self, screen, w, h, color):
        # Create surface with transparency
        cell_surface = pygame.Surface((w-1, h-1), pygame.SRCALPHA)

        if self.obstacle:
            # Obstacles with less transparency
            pygame.draw.rect(cell_surface, (0, 0, 0, 150), (0, 0, w-1, h-1), 0)
        else:
            # Other cells with more transparency
            r, g, b = color
            pygame.draw.rect(cell_surface, (r, g, b, 60), (0, 0, w-1, h-1), 0)

        # Border with transparency
        pygame.draw.rect(cell_surface, (255, 255, 255, 80), (0, 0, w-1, h-1), 1)

        # Draw surface on screen
        screen.blit(cell_surface, (self.x * w, self.y * h))

    def add_neighbors(self, grid):
        if self.x < COLS - 1:
            self.neighbors.append(grid[self.x + 1][self.y])
        if self.x > 0:
            self.neighbors.append(grid[self.x - 1][self.y])
        if self.y < ROWS - 1:
            self.neighbors.append(grid[self.x][self.y + 1])
        if self.y > 0:
            self.neighbors.append(grid[self.x][self.y - 1])


class AStarPathfinder:
    def __init__(self, grid, start, end):
        self.grid = grid
        self.start = start
        self.end = end

        self.open_set = []
        self.closed_set = set()
        self.current = None
        self.path = []
        self.found = False

        # Add start to open set
        heapq.heappush(self.open_set, (start.f, start))

    def heuristic(self, a, b):
        # Manhattan distance for grid movement
        return abs(a.x - b.x) + abs(a.y - b.y)

    def cost(self, a, b):
        # Cost is 1 for grid movement
        return 1

    def step(self):
        """Perform one step of the A* algorithm"""
        if len(self.open_set) > 0 and not self.found:
            # Get node with lowest f value
            _, self.current = heapq.heappop(self.open_set)

            if self.current == self.end:
                self.found = True
                print("Path found!")
                return True

            self.closed_set.add(self.current)

            # For each neighbor...
            for neighbor in self.current.neighbors:
                if neighbor not in self.closed_set and not neighbor.obstacle:
                    tentative_g = self.current.g + self.cost(self.current, neighbor)

                    # Check if neighbor is in open set
                    in_open = any(node == neighbor for _, node in self.open_set)

                    if not in_open or tentative_g < neighbor.g:
                        neighbor.parent = self.current
                        neighbor.g = tentative_g
                        neighbor.h = self.heuristic(neighbor, self.end)
                        neighbor.f = neighbor.g + neighbor.h

                        if not in_open:
                            heapq.heappush(self.open_set, (neighbor.f, neighbor))

        elif len(self.open_set) == 0 and not self.found:
            print("No solution found")
            self.found = True
            return True

        return self.found

    def get_path(self):
        """Reconstruct path from end to start"""
        if not self.current:
            return []

        path = []
        temp = self.current
        while temp:
            path.append(temp)
            temp = temp.parent
        return path

    def get_open_nodes(self):
        """Return list of nodes in open set"""
        return [node for _, node in self.open_set]


def load_obstacles_from_file(filename):
    """Load obstacles from file"""
    obstacles = []
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
                            obstacles.append((x, y))
                        except ValueError:
                            print(f"Error converting coordinates: {line}")
        return obstacles
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return []


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

                return start, end
    except (FileNotFoundError, ValueError, IndexError) as e:
        print(f"Error loading points from {filename}: {e}")

    # Default values if file doesn't exist or has errors
    return None, None


def setup(obstacle_file, points_file):
    """Create grid and populate with cells"""
    grid = []

    # Create grid (ROWS x COLS)
    for i in range(COLS):
        row = []
        for j in range(ROWS):
            row.append(None)
        grid.append(row)

    # Populate with cells
    for i in range(COLS):
        for j in range(ROWS):
            grid[i][j] = Cell(i, j)

    # Load obstacles from file
    obstacles = load_obstacles_from_file(obstacle_file)
    for x, y in obstacles:
        if 0 <= x < COLS and 0 <= y < ROWS:
            grid[x][y].obstacle = True

    # Calculate neighbors for each cell
    for i in range(COLS):
        for j in range(ROWS):
            grid[i][j].add_neighbors(grid)

    # Load or set start and end points
    start_pos, end_pos = load_points_from_file(points_file)

    if start_pos is None or end_pos is None:
        # Default positions
        start_pos = (64, 15)  # house
        end_pos = (6, 51)     # chicken coop
        print(f"Using default start {start_pos} and end {end_pos} positions")
    else:
        print(f"Loaded start {start_pos} and end {end_pos} from file")

    start = grid[start_pos[0]][start_pos[1]]
    end = grid[end_pos[0]][end_pos[1]]
    start.obstacle = False
    end.obstacle = False

    return grid, start, end


def main():
    """Main function"""
    # File paths
    obstacle_file = "data/obstacles.txt"
    points_file = "data/points.txt"

    # Pygame configuration
    pygame.init()
    screen_width = 1280
    screen_height = 1040
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("A* Pathfinding Visualization")

    # Load and resize background image
    try:
        bg_image = pygame.image.load('data/farm.png')
        bg_image = pygame.transform.scale(bg_image, (screen_width, screen_height))
    except pygame.error as e:
        print(f"Error loading background image: {e}")
        print("Continuing without background image")
        bg_image = None

    # Calculate exact cell size
    w = screen_width // COLS
    h = screen_height // ROWS

    clock = pygame.time.Clock()

    # Setup grid and pathfinder
    grid, start, end = setup(obstacle_file, points_file)
    pathfinder = AStarPathfinder(grid, start, end)

    # Font for instructions
    font = pygame.font.SysFont('Arial', 18)
    instructions = [
        "A* Pathfinding Algorithm",
        "Green: Open Set | Red: Closed Set | Blue: Path",
        "ESC: Exit"
    ]

    running = True

    while running:
        # Handle pygame events (user clicks X)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Draw background image first
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((50, 50, 50))

        # A* algorithm step
        pathfinder.step()

        # Render grid
        for i in range(COLS):
            for j in range(ROWS):
                cell = grid[i][j]
                if cell.obstacle:
                    cell.show(screen, w, h, (0, 0, 0))
                else:
                    cell.show(screen, w, h, (255, 255, 255))

        # Closed set in red
        for cell in pathfinder.closed_set:
            if not cell.obstacle:
                cell.show(screen, w, h, (255, 0, 0))

        # Open set in green
        for cell in pathfinder.get_open_nodes():
            if not cell.obstacle:
                cell.show(screen, w, h, (0, 255, 0))

        # Path in blue (reconstruct for visualization)
        path = pathfinder.get_path()
        for cell in path:
            cell.show(screen, w, h, (0, 0, 255))

        # Draw start and end markers
        start.show(screen, w, h, (0, 255, 255))  # Cyan
        end.show(screen, w, h, (255, 0, 255))    # Magenta

        # Draw instructions
        for i, text in enumerate(instructions):
            text_surface = font.render(text, True, (255, 255, 255))
            # Add background for readability
            bg_rect = text_surface.get_rect()
            bg_rect.topleft = (10, 10 + i*25)
            bg_surface = pygame.Surface((bg_rect.width + 10, bg_rect.height + 5))
            bg_surface.set_alpha(180)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, (5, 8 + i*25))
            screen.blit(text_surface, (10, 10 + i*25))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
