# trace.py
import sys
import copy
import types
import builtins

# --- configuration -------------------------------------
print("Trace your Python code!")
print("WARNING: This will run the code file you provide so ensure you trust it before entering")
user_file = input('Enter the name of the file to trace (e.g code.py): ')
EXCLUDE_SUFFIX = "x"

# --- helpers -------------------------------------------


def get_depth(frame):
  depth = 0
  f = frame
  while f:
    if f.f_code.co_filename.endswith(user_file):
      depth += 1
    f = f.f_back
  return depth

# -------------------------------------------------------
# Collect every change into `changes_local`
# -------------------------------------------------------


def collect_changes():
  global user_file
  changes_local = []

  _prev_locals: dict[int, dict] = {}
  _prev_globals: dict[str, object] = {}
  last_logged: dict[str, object] = {}

  # capture print output ---------------------------------
  real_print = builtins.print

  def log_print(*args, sep=" ", end="\n", **kw):
    text = sep.join(str(a) for a in args)
    if last_logged.get('OUT') != text:
      changes_local.append(('OUT', text))
      last_logged['OUT'] = text

  # tracer ------------------------------------------------
  def _trace(frame, event, arg):
    co = frame.f_code
    src = co.co_filename
    # skip non‑user frames and internal comprehensions
    if not src.endswith(user_file):
      return _trace
    if co.co_name != '<module>' and co.co_name.startswith('<'):
      return _trace

    fid = id(frame)

    # --- call -----------------------------------------
    if event == 'call' and co.co_name != '<module>':
      depth = get_depth(frame)
      if last_logged.get('CS_DEPTH') != depth:
        changes_local.append(('CS_DEPTH', depth))
        last_logged['CS_DEPTH'] = depth
      return _trace

    # --- return ---------------------------------------
    if event == 'return' and co.co_name != '<module>':
      parent = frame.f_back
      depth_after = get_depth(
          parent) if parent and parent.f_code.co_filename.endswith(user_file) else 0
      if last_logged.get('CS_DEPTH') != depth_after:
        changes_local.append(('CS_DEPTH', depth_after))
        last_logged['CS_DEPTH'] = depth_after
      # restore caller locals (snapshot)
      if parent and parent.f_code.co_filename.endswith(user_file):
        for var, val in parent.f_locals.items():
          if var.startswith('__') and var.endswith('__'):
            continue
          if var.endswith('x') or isinstance(
                  val, types.FunctionType):
            continue
          if last_logged.get(var) != val:
            changes_local.append((var, copy.deepcopy(val)))
            last_logged[var] = copy.deepcopy(val)
      # return value
      changes_local.append(('RET', arg))
      last_logged['RET'] = arg
      return _trace

    # --- line -----------------------------------------
    if event == 'line':
      locs = frame.f_locals
      prev = _prev_locals.setdefault(fid, {})
      # detect local mutations
      for var, val in locs.items():
        if var.startswith('__') and var.endswith('__'):
          continue
        if var.endswith(EXCLUDE_SUFFIX) or isinstance(
                val, types.FunctionType):
          continue
        if var not in prev or prev[var] != val:
          if last_logged.get(var) != val:
            changes_local.append((var, copy.deepcopy(val)))
            last_logged[var] = copy.deepcopy(val)
      _prev_locals[fid] = copy.deepcopy(locs)

      # detect global mutations (for module frame only)
      g = frame.f_globals
      for gvar, gval in g.items():
        if gvar.startswith('__') and gvar.endswith('__'):
          continue
        if gvar.endswith(EXCLUDE_SUFFIX) or isinstance(
                gval, types.FunctionType):
          continue
        if gvar not in _prev_globals or _prev_globals[gvar] != gval:
          if last_logged.get(gvar) != gval:
            changes_local.append((gvar, copy.deepcopy(gval)))
            last_logged[gvar] = copy.deepcopy(gval)
          _prev_globals[gvar] = copy.deepcopy(gval)
      return _trace

    return _trace

  while True:
    try:
      with open(user_file) as f:
        # run user code with tracer --------------------------------
        builtins.print = log_print
        sys.settrace(_trace)
        namespace = {}
        exec(compile(f.read(), user_file, 'exec'), namespace)
        break
    except SystemExit:
      break
    except Exception as e:
      print(f"Error opening file for execution: {e}")
      user_file = input(
          'Enter the name of the file to trace (e.g code.py): ')
      continue

  sys.settrace(None)
  builtins.print = real_print
  return changes_local

# -------------------------------------------------------
# Build ordered columns: CS_DEPTH | vars | RET | OUT
# -------------------------------------------------------


def build_columns(changes):
  seen = []
  for n, _ in changes:
    if n not in seen:
      seen.append(n)
  ordered = []
  if 'CS_DEPTH' in seen:
    ordered.append('CS_DEPTH')
  ordered.extend([c for c in seen if c not in ('CS_DEPTH', 'RET', 'OUT')])
  if 'RET' in seen:
    ordered.append('RET')
  if 'OUT' in seen:
    ordered.append('OUT')
  return ordered

# -------------------------------------------------------
# Optional user‑defined ordering of variable columns
# -------------------------------------------------------


def reorder_columns(columns):
  """
  Let the user specify an ordering for the *variable* columns.
  CS_DEPTH (if present) stays on the far left, RET & OUT stay on the far right.
  """
  var_cols = [c for c in columns if c not in ('CS_DEPTH', 'RET', 'OUT')]
  if not var_cols:
    return columns   # nothing to reorder

  ans = input(
      "Re‑order variable columns before tracing? (y/N): ").strip().lower()
  if ans != 'y':
    return columns

  # show numbered list
  print("\nVariable columns:")
  for i, v in enumerate(var_cols, 1):
    print(f"{i}) {v}")

  prompt = ("enter a comma‑separated string for variables to appear first "
            "(others will follow), e.g. 2,5,1: ")
  raw = input(prompt)

  try:
    numbers = [int(x.strip()) for x in raw.split(',') if x.strip()]
    if (not numbers or
        any(n < 1 or n > len(var_cols) for n in numbers) or
            len(set(numbers)) != len(numbers)):
      raise ValueError

    first_part = [var_cols[n - 1] for n in numbers]
    remainder = [v for v in var_cols if v not in first_part]

    new_cols = []
    if 'CS_DEPTH' in columns:
      new_cols.append('CS_DEPTH')
    new_cols.extend(first_part + remainder)
    if 'RET' in columns:
      new_cols.append('RET')
    if 'OUT' in columns:
      new_cols.append('OUT')
    return new_cols

  except ValueError:
    print("invalid entry, using default ordering...")
    return columns


# -------------------------------------------------------
# Interactive replay
# -------------------------------------------------------
all_changes = collect_changes()
columns = build_columns(all_changes)
columns = reorder_columns(columns)
row = {c: '' for c in columns}
rows = []

# -------------------------------------------------------
# Replace True/False with T/F for printing (recursively)
# -------------------------------------------------------


def fmt_bool(obj):
  """Return a string where every boolean True/False becomes T/F."""
  if isinstance(obj, bool):
    return 'T' if obj else 'F'
  if isinstance(obj, dict):
    pairs = (f"{fmt_bool(k)}: {fmt_bool(v)}" for k, v in obj.items())
    return '{' + ', '.join(pairs) + '}'
  if isinstance(obj, (list, tuple, set)):
    inner = ', '.join(fmt_bool(x) for x in obj)
    open_br, close_br = (
        '[', ']') if isinstance(
        obj, list) else (
        '(', ')') if isinstance(
        obj, tuple) else (
        '{', '}')
    # preserve trailing comma for 1‑tuples if you like, but not essential
    return f"{open_br}{inner}{close_br}"
  return str(obj)


def display(rows):
  # width calculation
  widths = {c: max(len(fmt_bool(r.get(c, ''))) for r in rows + [{c: c}]) + 2
            for c in columns}

  sep = '+' + '+'.join('-' * widths[c] for c in columns) + '+'
  header = '|' + ''.join(f' {c}'.ljust(widths[c]) + '|' for c in columns)
  print(sep)
  print(header)
  print(sep)
  for r in rows:
    print(
        '|' +
        ''.join(
            f' {fmt_bool(r.get(c, ""))}'.ljust(
                widths[c]) +
            '|' for c in columns)
    )

  print(sep)


for name, val in all_changes:
  if name == 'CS_DEPTH':
    if val > 0:
      if any(row.values()):
        rows.append(row)
      row = {c: '' for c in columns}
      row['CS_DEPTH'] = val - 1
      display(rows + [row])
      input()
    continue
  if name == 'RET':
    if any(row.values()):
      rows.append(row)
    row = {c: '' for c in columns}
    row['RET'] = val
    display(rows + [row])
    input()
    continue
  if name == 'OUT':
    if row.get('OUT', ''):
      rows.append(row)
      row = {c: '' for c in columns}
    row['OUT'] = val
    display(rows + [row])
    input()
    continue
  current_cell = row.get(name, '')
  if current_cell != '' and current_cell != val:
    rows.append(row)
    row = {c: '' for c in columns}
  row[name] = val
  display(rows + [row])
  input()

if any(row.values()):
  rows.append(row)

print('Final trace table:')
display(rows)
