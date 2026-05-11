#!/usr/bin/env python3
"""
Simplex Method Applet
=====================
A self-contained Flask web application that solves LP problems
using the Simplex Method and displays successive tableaux.

Usage:
    pip install flask
    python simplex_applet.py
    Open http://127.0.0.1:5000 in your browser
"""

from flask import Flask, request, jsonify
from fractions import Fraction
import json

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# Core Simplex Engine (exact arithmetic via fractions.Fraction)
# ─────────────────────────────────────────────────────────────

def run_simplex(c, A, b, var_names):
    """
    Solve max c^T x subject to Ax <= b, x >= 0 (canonical / standard form).
    Returns a list of step dicts, one per tableau shown.
    All arithmetic is exact (Fraction).
    """
    m = len(A)          # number of constraints
    n = len(c)          # number of decision variables
    total = n + m       # decision vars + slack vars

    # Convert to Fraction for exact arithmetic
    c  = [Fraction(v) for v in c]
    A  = [[Fraction(v) for v in row] for row in A]
    b  = [Fraction(v) for v in b]

    slack_names = [f"s{i+1}" for i in range(m)]
    all_names   = var_names + slack_names

    # Tableau: (m+1) rows × (total+1) cols
    # Rows 0..m-1 : constraints  |  Row m : objective (negated c for min-form)
    tab = [[Fraction(0)] * (total + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            tab[i][j] = A[i][j]
        tab[i][n + i] = Fraction(1)   # slack identity
        tab[i][total]  = b[i]
    for j in range(n):
        tab[m][j] = -c[j]             # negated objective coefficients

    basis = list(range(n, n + m))     # slacks are initial basis

    steps = []

    def fmt(v):
        """Format a Fraction nicely."""
        if v.denominator == 1:
            return str(v.numerator)
        return f"{v.numerator}/{v.denominator}"

    def snapshot(pivot_row, pivot_col, message, state):
        step = {
            "tableau": [[fmt(tab[i][j]) for j in range(total + 1)] for i in range(m + 1)],
            "basis":   [all_names[basis[i]] for i in range(m)],
            "all_names": all_names,
            "pivot_row": pivot_row,
            "pivot_col": pivot_col,
            "message":   message,
            "state":     state,
            "m": m,
            "n": total,
            "obj_value": fmt(tab[m][total]),
        }
        steps.append(step)

    snapshot(None, None,
             "Initial canonical tableau. Slack variables added. "
             "Identify the most negative entry in the objective row (z-row) to find the entering variable.",
             "initial")

    for iteration in range(200):
        # ── Optimality check: most negative reduced cost ──────
        enter_col  = -1
        most_neg   = Fraction(0)
        for j in range(total):
            if tab[m][j] < most_neg:
                most_neg  = tab[m][j]
                enter_col = j

        if enter_col == -1:
            snapshot(None, None,
                     f"All reduced costs ≥ 0. Optimal solution reached. "
                     f"Objective z* = {fmt(tab[m][total])}.",
                     "optimal")
            break

        # ── Minimum ratio test ────────────────────────────────
        leave_row = -1
        min_ratio = None
        for i in range(m):
            if tab[i][enter_col] > 0:
                ratio = tab[i][total] / tab[i][enter_col]
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    leave_row = i

        if leave_row == -1:
            snapshot(enter_col, None,
                     f"Entering variable {all_names[enter_col]} has all non-positive "
                     f"column coefficients — no finite minimum ratio exists. "
                     f"The problem is UNBOUNDED.",
                     "unbounded")
            break

        pivot_val = tab[leave_row][enter_col]
        snapshot(leave_row, enter_col,
                 f"Entering: {all_names[enter_col]} (col {enter_col+1})  |  "
                 f"Leaving: {all_names[basis[leave_row]]} (row {leave_row+1})  |  "
                 f"Pivot element = {fmt(pivot_val)}  |  "
                 f"Min ratio = {fmt(min_ratio)}.",
                 "pivot")

        # ── Pivot operation ───────────────────────────────────
        for j in range(total + 1):
            tab[leave_row][j] /= pivot_val

        for i in range(m + 1):
            if i != leave_row and tab[i][enter_col] != 0:
                factor = tab[i][enter_col]
                for j in range(total + 1):
                    tab[i][j] -= factor * tab[leave_row][j]

        basis[leave_row] = enter_col

        snapshot(None, None,
                 f"Pivot complete. Basis updated: {all_names[enter_col]} replaces "
                 f"{all_names[basis[leave_row]]}. "
                 f"Check objective row for next entering variable.",
                 "after_pivot")

    return steps


# ─────────────────────────────────────────────────────────────
# Flask Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/solve", methods=["POST"])
def solve():
    try:
        data      = request.get_json()
        c_raw     = data["c"]
        A_raw     = data["A"]
        b_raw     = data["b"]
        var_names = data.get("var_names", [])

        c = [Fraction(v) for v in c_raw]
        A = [[Fraction(v) for v in row] for row in A_raw]
        b = [Fraction(v) for v in b_raw]

        n = len(c)
        m = len(A)

        if not var_names:
            var_names = [f"x{i+1}" for i in range(n)]
        if len(var_names) != n:
            return jsonify({"error": f"Expected {n} variable names, got {len(var_names)}."}), 400
        if any(len(row) != n for row in A):
            return jsonify({"error": "Each constraint row must have the same number of coefficients as the objective."}), 400
        if len(b) != m:
            return jsonify({"error": "Number of RHS values must equal number of constraint rows."}), 400
        if any(v < 0 for v in b):
            return jsonify({"error": "All RHS values must be ≥ 0 (canonical form required)."}), 400

        steps = run_simplex(c, A, b, var_names)
        return jsonify({"steps": steps})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ─────────────────────────────────────────────────────────────
# Embedded HTML/CSS/JS (single-file app)
# ─────────────────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Simplex Method Applet</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@600&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,300&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#1a1a2e;--ink2:#3d3d5c;--ink3:#7070a0;
  --paper:#faf9f6;--paper2:#f0ede6;--paper3:#e5e0d5;
  --accent:#2e4057;--accent2:#4a7c6f;--accent3:#c0392b;
  --gold:#b8860b;--enter:#1a5276;--leave:#922b21;--pivot:#1d6a3a;
  --optimal:#145a32;--unbounded:#7b241c;
  --radius:6px;--mono:'DM Mono',monospace;
}
body{font-family:'Source Serif 4',Georgia,serif;background:var(--paper);color:var(--ink);min-height:100vh}

/* ── Layout ── */
.shell{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
.sidebar{background:var(--accent);color:#e8e4da;padding:2rem 1.5rem;display:flex;flex-direction:column;gap:1.5rem;position:sticky;top:0;height:100vh;overflow-y:auto}
.main{padding:2rem 2.5rem;overflow-y:auto}

/* ── Sidebar ── */
.logo{font-family:'Playfair Display',serif;font-size:1.5rem;color:#f0e8d0;line-height:1.2;border-bottom:1px solid rgba(255,255,255,.15);padding-bottom:1rem}
.logo span{display:block;font-family:'Source Serif 4',serif;font-size:.8rem;font-weight:300;color:rgba(240,232,208,.6);margin-top:.3rem;font-style:italic}
label{display:block;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(240,232,208,.55);margin-bottom:.35rem;font-family:var(--mono)}
input,textarea,select{width:100%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);border-radius:var(--radius);color:#f0e8d0;font-family:var(--mono);font-size:.82rem;padding:.5rem .7rem;outline:none;transition:border-color .2s}
input:focus,textarea:focus{border-color:rgba(255,255,255,.5);background:rgba(255,255,255,.13)}
textarea{resize:vertical;min-height:90px}
.hint{font-size:.7rem;color:rgba(240,232,208,.4);margin-top:.3rem;font-style:italic}
.examples-title{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(240,232,208,.55);font-family:var(--mono)}
.ex-btn{display:block;width:100%;text-align:left;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:var(--radius);color:#d4cfc4;font-family:var(--mono);font-size:.75rem;padding:.45rem .7rem;cursor:pointer;margin-top:.4rem;transition:all .15s}
.ex-btn:hover{background:rgba(255,255,255,.15);color:#f0e8d0}
.solve-btn{width:100%;padding:.75rem;background:var(--accent2);border:none;border-radius:var(--radius);color:#fff;font-family:'Playfair Display',serif;font-size:1rem;font-weight:600;cursor:pointer;letter-spacing:.04em;transition:filter .2s;margin-top:.5rem}
.solve-btn:hover{filter:brightness(1.15)}
.solve-btn:active{filter:brightness(.9)}

/* ── Main area ── */
.page-title{font-family:'Playfair Display',serif;font-size:1.8rem;color:var(--accent);margin-bottom:.3rem}
.page-sub{font-size:.9rem;color:var(--ink3);font-style:italic;margin-bottom:1.5rem}
.error-box{background:#fdecea;border:1px solid #f5c6c2;border-radius:var(--radius);padding:.75rem 1rem;color:var(--accent3);font-family:var(--mono);font-size:.8rem;margin-bottom:1rem}

/* ── Step navigation ── */
.nav-bar{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap;margin-bottom:1.2rem}
.nav-btn{padding:.4rem .9rem;border:1px solid var(--paper3);background:var(--paper2);border-radius:var(--radius);font-family:var(--mono);font-size:.78rem;cursor:pointer;color:var(--ink2);transition:all .15s}
.nav-btn:hover:not(:disabled){background:var(--accent);color:#fff;border-color:var(--accent)}
.nav-btn:disabled{opacity:.35;cursor:default}
.nav-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.step-counter{font-family:var(--mono);font-size:.78rem;color:var(--ink3)}
.step-pills{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:1.2rem}
.pill{padding:.25rem .65rem;border-radius:20px;border:1px solid var(--paper3);background:var(--paper2);font-family:var(--mono);font-size:.72rem;cursor:pointer;color:var(--ink3);transition:all .15s}
.pill:hover{border-color:var(--accent);color:var(--accent)}
.pill.active{background:var(--accent);color:#fff;border-color:var(--accent)}

/* ── Tableau card ── */
.tab-card{background:#fff;border:1px solid var(--paper3);border-radius:10px;overflow:hidden;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.tab-header{padding:.65rem 1.2rem;display:flex;justify-content:space-between;align-items:center;font-family:var(--mono);font-size:.78rem}
.tab-header.initial  {background:#2e4057;color:#e8e4da}
.tab-header.pivot    {background:#1a5276;color:#d6eaf8}
.tab-header.after_pivot{background:#1a5e45;color:#d5f5e3}
.tab-header.optimal  {background:#145a32;color:#a9dfbf}
.tab-header.unbounded{background:#7b241c;color:#f5b7b1}
.tab-msg{padding:.6rem 1.2rem;font-size:.82rem;color:var(--ink2);border-bottom:1px solid var(--paper3);font-style:italic;background:var(--paper)}
.tab-scroll{overflow-x:auto;padding:.5rem}

/* ── Table styling ── */
table{border-collapse:collapse;font-family:var(--mono);font-size:.8rem;min-width:100%}
th{background:#f5f3ee;padding:.45rem .8rem;text-align:center;border:1px solid #ddd;color:var(--accent);font-weight:500;white-space:nowrap}
th.enter-col{background:#d6eaf8;color:var(--enter)}
td{padding:.4rem .8rem;text-align:right;border:1px solid #e8e4da;color:var(--ink);white-space:nowrap}
td.basis-cell{text-align:center;font-weight:500;background:#f9f7f2;color:var(--accent)}
td.enter-col{background:#eaf4fc;color:var(--enter)}
td.leave-row{background:#fff5f4}
td.pivot-cell{background:#c8f0d8 !important;color:var(--pivot);font-weight:700;outline:2px solid var(--pivot)}
tr.obj-row td{background:#f0ede6;font-weight:500}
tr.obj-row td.enter-col{background:#d6eaf8}
td.neg-rc{color:var(--enter);font-weight:500}
td.pos-rc{color:var(--leave)}

/* ── Result boxes ── */
.result-optimal{background:#eafaf1;border:1px solid #a9dfbf;border-radius:var(--radius);padding:.8rem 1.2rem;margin:.75rem 1.2rem;font-family:var(--mono);font-size:.8rem;color:var(--optimal)}
.result-unbounded{background:#fdedec;border:1px solid #f5b7b1;border-radius:var(--radius);padding:.8rem 1.2rem;margin:.75rem 1.2rem;font-family:var(--mono);font-size:.8rem;color:var(--unbounded)}

/* ── Legend ── */
.legend{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;margin-top:1.5rem;padding:1rem 1.2rem;background:var(--paper2);border-radius:var(--radius);border:1px solid var(--paper3)}
.legend-item{display:flex;align-items:center;gap:.4rem;font-family:var(--mono);font-size:.73rem;color:var(--ink3)}
.legend-swatch{width:14px;height:14px;border-radius:3px;flex-shrink:0}

@media(max-width:750px){
  .shell{grid-template-columns:1fr}
  .sidebar{position:static;height:auto}
}
</style>
</head>
<body>
<div class="shell">
<!-- ───────── SIDEBAR ───────── -->
<aside class="sidebar">
  <div class="logo">Simplex<br>Tableau Solver
    <span>Step-by-step LP solver · Python + Flask</span>
  </div>

  <div>
    <label>Objective coefficients c (maximise c·x)</label>
    <input id="c-input" value="5 4" placeholder="e.g. 5 4 3"/>
    <div class="hint">Space or comma separated</div>
  </div>

  <div>
    <label>Variable names (optional)</label>
    <input id="var-input" value="x1 x2" placeholder="e.g. x1 x2 x3"/>
  </div>

  <div>
    <label>Constraint matrix A  (Ax ≤ b)</label>
    <textarea id="A-input">6 4
1 2</textarea>
    <div class="hint">One constraint per line; coefficients space- or comma-separated</div>
  </div>

  <div>
    <label>RHS vector b  (all values ≥ 0)</label>
    <input id="b-input" value="24 6" placeholder="e.g. 24 6 10"/>
  </div>

  <button class="solve-btn" onclick="solve()">Solve →</button>

  <div>
    <div class="examples-title">Load example</div>
    <button class="ex-btn" onclick="loadEx(0)">Ex 1 · 2 vars, 2 constraints</button>
    <button class="ex-btn" onclick="loadEx(1)">Ex 2 · 3 vars, 3 constraints</button>
    <button class="ex-btn" onclick="loadEx(2)">Ex 3 · Unbounded problem</button>
    <button class="ex-btn" onclick="loadEx(3)">Ex 4 · Degenerate case</button>
  </div>
</aside>

<!-- ───────── MAIN ───────── -->
<main class="main">
  <h1 class="page-title">Successive Simplex Tableaux</h1>
  <p class="page-sub">Canonical form: max c<sup>T</sup>x subject to Ax ≤ b, x ≥ 0.
     Slack variables s<sub>i</sub> are added automatically.</p>

  <div id="error-area"></div>
  <div id="nav-area" style="display:none">
    <div class="nav-bar">
      <button class="nav-btn" id="btn-prev" onclick="step(-1)">← Prev</button>
      <button class="nav-btn" id="btn-next" onclick="step(1)">Next →</button>
      <button class="nav-btn" id="btn-all"  onclick="toggleAll()">Show all</button>
      <span class="step-counter" id="step-counter"></span>
    </div>
    <div class="step-pills" id="step-pills"></div>
  </div>
  <div id="tableau-area"></div>
  <div class="legend" id="legend" style="display:none">
    <div class="legend-item"><div class="legend-swatch" style="background:#d6eaf8;border:1px solid #aed6f1"></div>Entering variable column</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#fff5f4;border:1px solid #f5c6c2"></div>Leaving variable row</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#c8f0d8;border:2px solid #1d6a3a"></div>Pivot element</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#eaf4fc"></div>neg. reduced cost</div>
  </div>
</main>
</div>

<script>
const EXAMPLES = [
  {c:"5 4",    A:"6 4\n1 2",        b:"24 6",    v:"x1 x2"},
  {c:"3 2 5",  A:"1 2 1\n3 0 2\n1 4 0", b:"430 460 420", v:"x1 x2 x3"},
  {c:"2 1",    A:"-1 1\n1 -2",      b:"1 2",     v:"x1 x2"},
  {c:"2 3",    A:"1 2\n2 1\n1 1",   b:"4 4 3",   v:"x1 x2"},
];

function loadEx(i){
  const e=EXAMPLES[i];
  document.getElementById('c-input').value=e.c;
  document.getElementById('A-input').value=e.A;
  document.getElementById('b-input').value=e.b;
  document.getElementById('var-input').value=e.v;
  clearResults();
}

function clearResults(){
  document.getElementById('error-area').innerHTML='';
  document.getElementById('tableau-area').innerHTML='';
  document.getElementById('nav-area').style.display='none';
  document.getElementById('legend').style.display='none';
}

function parseLine(s){return s.trim().split(/[\s,]+/).map(Number);}

let allSteps=[], current=0, showAll=false;

async function solve(){
  clearResults();
  const cArr   = parseLine(document.getElementById('c-input').value);
  const bArr   = parseLine(document.getElementById('b-input').value);
  const ALines = document.getElementById('A-input').value.trim().split('\n');
  const AArr   = ALines.map(parseLine);
  const vRaw   = document.getElementById('var-input').value.trim();
  const vArr   = vRaw ? vRaw.split(/[\s,]+/) : [];

  try{
    const res = await fetch('/solve',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({c:cArr,A:AArr,b:bArr,var_names:vArr})
    });
    const data = await res.json();
    if(data.error){showError(data.error);return;}
    allSteps = data.steps;
    current  = 0;
    showAll  = false;
    buildNav();
    render();
  }catch(err){showError('Network error: '+err.message);}
}

function showError(msg){
  document.getElementById('error-area').innerHTML=
    `<div class="error-box">⚠ ${msg}</div>`;
}

function buildNav(){
  const nav = document.getElementById('nav-area');
  nav.style.display='';
  // pills
  const pills = document.getElementById('step-pills');
  pills.innerHTML = allSteps.map((_,i)=>
    `<span class="pill ${i===0?'active':''}" id="pill-${i}" onclick="jumpTo(${i})">T${i+1}</span>`
  ).join('');
  updateNav();
}

function updateNav(){
  document.getElementById('btn-prev').disabled = showAll||current===0;
  document.getElementById('btn-next').disabled = showAll||current===allSteps.length-1;
  document.getElementById('btn-all').textContent = showAll?'Step mode':'Show all';
  document.getElementById('step-counter').textContent =
    showAll ? `${allSteps.length} tableaux` : `Tableau ${current+1} / ${allSteps.length}`;
  allSteps.forEach((_,i)=>{
    const p=document.getElementById(`pill-${i}`);
    if(p) p.className='pill'+((!showAll&&i===current)||showAll?' active':'');
  });
}

function step(d){current=Math.max(0,Math.min(allSteps.length-1,current+d));updateNav();render();}
function jumpTo(i){showAll=false;current=i;updateNav();render();}
function toggleAll(){showAll=!showAll;updateNav();render();}

function render(){
  const area = document.getElementById('tableau-area');
  const toShow = showAll ? allSteps : [allSteps[current]];
  const offset = showAll ? 0 : current;
  area.innerHTML = toShow.map((s,i)=>buildTableauHTML(s,offset+i)).join('');
  document.getElementById('legend').style.display='';
}

function buildTableauHTML(step, idx){
  const {tableau,basis,all_names,pivot_row,pivot_col,message,state,m,n,obj_value}=step;
  const stateLabel={initial:'Initial Tableau',pivot:'Pivot Step',after_pivot:'After Pivot',optimal:'✓ Optimal',unbounded:'✗ Unbounded'}[state]||state;

  // Header row of table
  let thead = `<tr><th>Basis</th>`;
  all_names.forEach((v,j)=>{
    const cls = j===pivot_col?'enter-col':'';
    thead += `<th class="${cls}">${v}</th>`;
  });
  thead += `<th>RHS</th></tr>`;

  // Constraint rows
  let tbody='';
  for(let i=0;i<m;i++){
    const isLeave = i===pivot_row;
    let row=`<tr class="${isLeave?'leave-row':''}">`;
    row+=`<td class="basis-cell" style="${isLeave?'color:var(--leave);':''}"">${basis[i]}</td>`;
    tableau[i].slice(0,n).forEach((v,j)=>{
      const isPivot=isLeave&&j===pivot_col;
      let cls='';
      if(isPivot) cls='pivot-cell';
      else if(isLeave) cls='leave-row';
      else if(j===pivot_col) cls='enter-col';
      row+=`<td class="${cls}">${v}</td>`;
    });
    row+=`<td style="font-weight:500">${tableau[i][n]}</td>`;
    row+='</tr>';
    tbody+=row;
  }

  // Objective row
  let objRow=`<tr class="obj-row"><td class="basis-cell">z−row</td>`;
  tableau[m].slice(0,n).forEach((v,j)=>{
    const val=parseFloat(v.includes('/')?eval(v):v);
    let cls = j===pivot_col?'enter-col':'';
    let style='';
    if(val<-1e-9) style='color:var(--enter);font-weight:500';
    else if(val>1e-9) style='color:var(--ink3)';
    objRow+=`<td class="${cls}" style="${style}">${v}</td>`;
  });
  objRow+=`<td style="font-weight:700;color:var(--accent)">${tableau[m][n]}</td></tr>`;

  // Result box
  let resultBox='';
  if(state==='optimal'){
    const sol=basis.map((b,i)=>`${b} = ${tableau[i][n]}`).join(' &nbsp;|&nbsp; ');
    resultBox=`<div class="result-optimal">Optimal: &nbsp;${sol} &nbsp;|&nbsp; <strong>z* = ${obj_value}</strong></div>`;
  }
  if(state==='unbounded'){
    resultBox=`<div class="result-unbounded">The problem is <strong>unbounded</strong>. The objective value can grow without limit.</div>`;
  }

  return `
<div class="tab-card">
  <div class="tab-header ${state}">
    <span>Tableau ${idx+1} — ${stateLabel}</span>
    <span style="opacity:.7">${allSteps.length} total</span>
  </div>
  <div class="tab-msg">${message}</div>
  <div class="tab-scroll">
    <table><thead>${thead}</thead><tbody>${tbody}${objRow}</tbody></table>
  </div>
  ${resultBox}
</div>`;
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("=" * 55)
    print("  Simplex Method Applet")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 55)
    app.run(debug=True, port=5000)
