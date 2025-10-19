# 🎮 Pac-Man AI Game

A Python implementation of Pac-Man featuring intelligent ghost behaviors using different pathfinding algorithms (DFS, BFS, A*). Built with tkinter for desktop gameplay.

## 🚀 Features

- **Three AI Algorithms**: DFS (Easy), BFS (Medium), A* (Hard)
- **Smart Ghosts**: Territory-based behavior and special chasing ghosts
- **Real-time Combat**: Shoot beams, avoid projectiles, manage lives
- **Dynamic Difficulty**: Switch algorithms during gameplay
- **Classic Gameplay**: Collect pellets, avoid ghosts, survive!

## 🎯 Game Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move Pac-Man |
| Z | Shoot beam |
| 1/2/3 | Change difficulty (DFS/BFS/A*) |
| Escape | Pause/Resume |
| Enter | Start game from menu |

## 🛠️ Installation & Running

### Prerequisites
- Python 3.6 or higher
- tkinter (usually included with Python)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/sabbirog/ai-game.git
cd ai-game

# Run the game
python game.py
```

### Alternative Installation
```bash
# No dependencies needed - uses only Python standard library
# Just run the game directly
python game.py
```

## 🧠 AI Algorithms

### Depth-First Search (DFS) - Easy Mode
- **Behavior**: Explores paths deeply before backtracking
- **Characteristics**: Not optimal, can get stuck in loops
- **Difficulty**: Easiest for players

### Breadth-First Search (BFS) - Medium Mode  
- **Behavior**: Explores all paths at current distance before going deeper
- **Characteristics**: Finds shortest path in unweighted grids
- **Difficulty**: Moderate challenge

### A* Search - Hard Mode
- **Behavior**: Uses heuristic to guide search toward goal
- **Characteristics**: Optimal and efficient pathfinding
- **Difficulty**: Most challenging for players

## 🏗️ Project Structure

```
ai-game/
├── game.py           # Main game logic and tkinter interface
├── pathfinding.py    # Pathfinding algorithms (DFS, BFS, A*)
├── index.html        # GitHub Pages landing page
└── README.md         # This file
```

## 🎮 Game Mechanics

- **Player**: Yellow Pac-Man with animated mouth
- **Ghosts**: Red regular ghosts (territory-based) and purple special ghosts (always chase)
- **Pellets**: Golden dots worth 10 points each
- **Lives**: 5 hearts displayed in top-left corner
- **Beams**: Yellow player beams, cyan ghost beams
- **Win Condition**: Collect all pellets
- **Lose Condition**: Run out of lives

## 🔧 Technical Details

- **Framework**: Python tkinter for GUI
- **Pathfinding**: Custom implementations of DFS, BFS, and A*
- **Threading**: Background ghost respawn timers
- **Animation**: Smooth Pac-Man mouth animation and ghost eye tracking
- **Collision Detection**: Real-time beam and entity collision handling

## 🌐 Web Version

This project includes an `index.html` file for GitHub Pages that provides:
- Project overview and features
- Installation instructions
- Algorithm explanations
- Download links

**Note**: The game itself runs as a Python desktop application and cannot be played directly in a web browser.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🎯 Future Enhancements

- [ ] Web-based version using HTML5 Canvas and JavaScript
- [ ] Additional pathfinding algorithms (Dijkstra, JPS)
- [ ] Sound effects and background music
- [ ] Multiple levels and mazes
- [ ] High score system
- [ ] Ghost AI learning capabilities

## 📧 Contact

Created by Sabbir Ahmed - feel free to reach out!

---

⭐ Star this repository if you found it helpful!