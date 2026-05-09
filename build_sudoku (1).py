#!/usr/bin/env python3
"""
Build the Sudoku project.

Usage:  python build_sudoku.py
Output: ./sudoku/

Layout:
  sudoku/
    solver.py       backtracking solver (is_valid, solve)
    generator.py    puzzle generator (uses solver) + DIFFICULTIES
    web.py          Flask app + routes (uses solver + generator)
    run.py          short entry point — starts the server
    templates/index.html
    README.md
    requirements.txt
"""

import os

OUT = "sudoku"

FILES = {}

FILES["solver.py"] = r'''def is_valid(board, row, col, num):
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == num:
                return False
    return True


def solve(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for n in range(1, 10):
                    if is_valid(board, r, c, n):
                        board[r][c] = n
                        if solve(board):
                            return True
                        board[r][c] = 0
                return False
    return True
'''

FILES["generator.py"] = r'''import random
import copy
from solver import is_valid

DIFFICULTIES = {
    "easy": 38,
    "intermediate": 46,
    "advanced": 52,
    "hard": 58,
}


def fill_board(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for n in nums:
                    if is_valid(board, r, c, n):
                        board[r][c] = n
                        if fill_board(board):
                            return True
                        board[r][c] = 0
                return False
    return True


def generate_puzzle(difficulty):
    if difficulty not in DIFFICULTIES:
        difficulty = "easy"
    full = [[0] * 9 for _ in range(9)]
    fill_board(full)
    solution = copy.deepcopy(full)
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    for r, c in cells[: DIFFICULTIES[difficulty]]:
        full[r][c] = 0
    return full, solution
'''

FILES["web.py"] = r'''import copy
from flask import Flask, render_template, request, jsonify
from solver import solve
from generator import generate_puzzle

app = Flask(__name__)


def is_valid_board(board):
    """Return True if board is a 9x9 grid of integers in 0-9."""
    if not isinstance(board, list) or len(board) != 9:
        return False
    for row in board:
        if not isinstance(row, list) or len(row) != 9:
            return False
        for v in row:
            if not isinstance(v, int) or v < 0 or v > 9:
                return False
    return True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/new", methods=["POST"])
def new_game():
    body = request.get_json(silent=True) or {}
    diff = body.get("difficulty", "easy")
    puzzle, solution = generate_puzzle(diff)
    return jsonify({"puzzle": puzzle, "solution": solution})


@app.route("/solve", methods=["POST"])
def solve_route():
    body = request.get_json(silent=True) or {}
    board = body.get("board")
    if not is_valid_board(board):
        return jsonify({"solved": None, "error": "Invalid board"})
    work = copy.deepcopy(board)
    if solve(work):
        return jsonify({"solved": work})
    return jsonify({"solved": None})


@app.route("/check", methods=["POST"])
def check_route():
    body = request.get_json(silent=True) or {}
    board = body.get("board")
    solution = body.get("solution")
    if not is_valid_board(board) or not is_valid_board(solution):
        return jsonify({"correct": False, "complete": False})
    complete = all(v != 0 for row in board for v in row)
    correct = complete and board == solution
    return jsonify({"correct": correct, "complete": complete})
'''

FILES["run.py"] = r'''#!/usr/bin/env python3
"""Entry point — links modules and starts the server."""
from web import app

if __name__ == "__main__":
    app.run(debug=True, port=5001)
'''

FILES["templates/index.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>Sudoku</title>
<style>
  body { font-family: sans-serif; padding: 20px; }
  table { border-collapse: collapse; margin: 10px 0; }
  td { border: 1px solid #999; padding: 0; width: 36px; height: 36px; text-align: center; }
  td.thick-right { border-right: 2px solid black; }
  td.thick-bottom { border-bottom: 2px solid black; }
  td.thick-left { border-left: 2px solid black; }
  td.thick-top { border-top: 2px solid black; }
  input { width: 34px; height: 34px; text-align: center; font-size: 18px; border: none; }
  input:focus { background: #def; outline: none; }
  .fixed { background: #eee; font-weight: bold; }
  #status { margin-top: 10px; }
</style>
</head>
<body>

<h1>Sudoku</h1>

<label>Difficulty:
  <select id="diff">
    <option value="easy">Easy</option>
    <option value="intermediate">Intermediate</option>
    <option value="advanced">Advanced</option>
    <option value="hard">Hard</option>
  </select>
</label>
<button onclick="newGame()">New Game</button>
<button onclick="checkBoard()">Check</button>
<button onclick="solveBoard()">Solve</button>
<button onclick="resetBoard()">Reset</button>

<div id="board"></div>
<div id="status"></div>

<script>
let solution = null;
let original = null;

function buildBoard(puzzle) {
  const div = document.getElementById('board');
  let html = '<table>';
  for (let r = 0; r < 9; r++) {
    html += '<tr>';
    for (let c = 0; c < 9; c++) {
      const classes = [];
      if (c === 2 || c === 5) classes.push('thick-right');
      if (r === 2 || r === 5) classes.push('thick-bottom');
      if (c === 0) classes.push('thick-left');
      if (r === 0) classes.push('thick-top');
      if (c === 8) classes.push('thick-right');
      if (r === 8) classes.push('thick-bottom');
      const val = puzzle[r][c];
      const fixed = val !== 0;
      const cls = classes.join(' ');
      if (fixed) {
        html += `<td class="${cls}"><input class="fixed" value="${val}" readonly id="c${r}-${c}"></td>`;
      } else {
        html += `<td class="${cls}"><input maxlength="1" id="c${r}-${c}"></td>`;
      }
    }
    html += '</tr>';
  }
  html += '</table>';
  div.innerHTML = html;
}

function readBoard() {
  const board = [];
  for (let r = 0; r < 9; r++) {
    const row = [];
    for (let c = 0; c < 9; c++) {
      const v = document.getElementById(`c${r}-${c}`).value;
      row.push(v && /^[1-9]$/.test(v) ? parseInt(v, 10) : 0);
    }
    board.push(row);
  }
  return board;
}

function writeBoard(board) {
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const inp = document.getElementById(`c${r}-${c}`);
      inp.value = board[r][c] === 0 ? '' : board[r][c];
    }
  }
}

async function newGame() {
  const diff = document.getElementById('diff').value;
  const res = await fetch('/new', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({difficulty: diff})
  });
  const data = await res.json();
  solution = data.solution;
  original = JSON.parse(JSON.stringify(data.puzzle));
  buildBoard(data.puzzle);
  document.getElementById('status').textContent = '';
}

async function solveBoard() {
  const board = readBoard();
  const res = await fetch('/solve', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: board})
  });
  const data = await res.json();
  if (data.solved) {
    writeBoard(data.solved);
    document.getElementById('status').textContent = 'Solved.';
  } else {
    document.getElementById('status').textContent = 'No solution found.';
  }
}

async function checkBoard() {
  const board = readBoard();
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: board, solution: solution})
  });
  const data = await res.json();
  let msg;
  if (data.correct) {
    msg = 'Correct! You solved it.';
  } else if (!data.complete) {
    msg = 'Board is not complete yet.';
  } else {
    msg = 'Not yet correct.';
  }
  document.getElementById('status').textContent = msg;
}

function resetBoard() {
  if (original) {
    buildBoard(original);
    document.getElementById('status').textContent = '';
  }
}

newGame();
</script>

</body>
</html>
'''

FILES["README.md"] = r'''# Sudoku

Simple Sudoku game with a generator, solver, and 4 difficulty levels.

## Setup

```
pip install -r requirements.txt
python run.py
```

Open http://localhost:5001 in your browser.

## Modules

| File           | Purpose                                                |
|----------------|--------------------------------------------------------|
| `solver.py`    | Backtracking solver — `is_valid`, `solve`              |
| `generator.py` | Puzzle generator — `fill_board`, `generate_puzzle`, `DIFFICULTIES` |
| `web.py`       | Flask app and routes                                   |
| `run.py`       | Entry point — imports `web.app` and starts the server  |

## Difficulty levels

| Difficulty   | Cells removed | Clues left |
|--------------|---------------|------------|
| Easy         | 38            | 43         |
| Intermediate | 46            | 35         |
| Advanced     | 52            | 29         |
| Hard         | 58            | 23         |

## Note

The generator removes random cells without guaranteeing a unique solution. For casual play this works fine, but at higher difficulties a puzzle may have more than one valid solution.
'''

FILES["requirements.txt"] = "flask\n"


def main():
    for rel, content in FILES.items():
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote", path)
    print("\nDone.")
    print("Next:")
    print("  cd", OUT)
    print("  pip install -r requirements.txt")
    print("  python run.py")


if __name__ == "__main__":
    main()
