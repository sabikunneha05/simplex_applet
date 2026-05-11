# 📊 Simplex Method Tableau Solver

An interactive web application built with **Python + Flask** that solves Linear Programming problems using the **Simplex Method**, displaying each successive tableau step-by-step until the optimal solution is found or the problem is concluded to be unbounded.

---

##  Features

- ✅ Accepts any LP problem in **canonical/standard form** (maximization)
- ✅ Automatically adds **slack variables**
- ✅ Displays **successive simplex tableaux** one by one
- ✅ Highlights the **entering variable**, **leaving variable**, and **pivot element** in each step
- ✅ Detects and reports **optimal solution** with variable values and objective value
- ✅ Detects and reports **unbounded** problems
- ✅ Uses **exact arithmetic** (`fractions.Fraction`) — no floating-point errors
- ✅ 4 built-in examples to explore immediately
- ✅ Step-by-step navigation (Prev / Next / Jump / Show All)

---

##  Getting Started

### Prerequisites

- Python 3.7 or higher
- pip

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOURUSERNAME/simplex-solver.git
cd simplex-solver
```

**2. Install dependencies**
```bash
pip install flask
```

**3. Run the app**
```bash
python simplex_applet.py
```

**4. Open your browser and go to**
```
http://127.0.0.1:5000
```

---

## Live Demo

The app is deployed and publicly accessible at:

```
http://YOURUSERNAME.pythonanywhere.com
```

No installation required — just open the link in any browser.

---

## 📐 How to Use

The app solves problems of the form:

```
Maximize:    z = c₁x₁ + c₂x₂ + ... + cₙxₙ
Subject to:  a₁₁x₁ + a₁₂x₂ + ... ≤ b₁
             a₂₁x₁ + a₂₂x₂ + ... ≤ b₂
             ...
             x₁, x₂, ... ≥ 0   and   all bᵢ ≥ 0
```

### Input fields

| Field | Description | Example |
|-------|-------------|---------|
| **Objective coefficients c** | Space-separated coefficients of the objective function | `5 4` |
| **Variable names** | Optional custom names for decision variables | `x1 x2` |
| **Constraint matrix A** | One constraint row per line | `6 4` then `1 2` |
| **RHS vector b** | Space-separated right-hand side values (all ≥ 0) | `24 6` |

### Navigation

| Button | Action |
|--------|--------|
| **Solve →** | Run the simplex algorithm |
| **Next / Prev** | Step forward or backward through tableaux |
| **T1, T2, …** | Jump directly to any tableau |
| **Show all** | Display all tableaux at once |

---

## 🔬 Example

**Problem:**
```
Maximize:   z = 5x₁ + 4x₂
Subject to: 6x₁ + 4x₂ ≤ 24
             x₁ + 2x₂ ≤ 6
            x₁, x₂ ≥ 0
```

**Input:**
- c: `5 4`
- A: `6 4` / `1 2`
- b: `24 6`

**Result:** `x₁ = 3, x₂ = 3/2, z* = 21`

---

##  Project Structure

```
simplex-solver/
│
└── simplex_applet.py     # Complete self-contained app (backend + frontend)
```

The entire application — Flask backend, Simplex engine, and HTML/CSS/JS frontend — lives in a **single Python file**. No templates folder, no static files, no extra dependencies beyond Flask.

---

## ⚙️ How It Works

1. **Input parsing** — User inputs are validated and converted to `Fraction` objects for exact arithmetic
2. **Slack variables** — Added automatically to convert `Ax ≤ b` to standard equality form
3. **Initial tableau** — Built with the constraint matrix, identity (slacks), and negated objective row
4. **Pivot selection** — Most negative reduced cost → entering variable; minimum ratio test → leaving variable
5. **Row operations** — Exact Gaussian elimination performed at each iteration
6. **Termination** — Stops when all reduced costs ≥ 0 (optimal) or no positive pivot exists (unbounded)

---

## ☁️ Deployment (PythonAnywhere)

1. Sign up free at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload `simplex_applet.py` via the **Files** tab
3. Open a **Bash console** and run:
   ```bash
   pip install flask --user
   ```
4. Go to **Web tab** → Add new web app → Manual configuration → Python 3.10
5. In the WSGI configuration file, replace everything with:
   ```python
   import sys
   sys.path.insert(0, '/home/YOURUSERNAME')
   from simplex_applet import application
   ```
6. Click **Reload** — your app is live at `http://YOURUSERNAME.pythonanywhere.com`

---

##  Built With

- [Python 3](https://www.python.org/) — Core language
- [Flask](https://flask.palletsprojects.com/) — Lightweight web framework
- `fractions.Fraction` — Exact rational arithmetic (standard library)
- Vanilla HTML / CSS / JavaScript — Frontend (no external frameworks)

---

## Author

**Sabikunneha**
- GitHub: [@YOURUSERNAME](https://github.com/sabikunneha05)

---

## 📄 License

This project is submitted as part of a university course assignment.
