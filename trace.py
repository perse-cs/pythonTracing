# trace.py
import sys
import copy
import types
import builtins

# --- configuration -------------------------------------
USER_FILE = input('Enter the name of the file to trace (e.g code.py): ')

# --- helpers -------------------------------------------


def get_depth(frame):
  depth = 0
  f = frame
  while f:
    if f.f_code.co_filename.endswith(USER_FILE):
      depth += 1
    f = f.f_back
  return depth

# -------------------------------------------------------
# Collect every change into `changes_local`
# -------------------------------------------------------


def collect_changes():
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
    return real_print(*args, sep=sep, end=end, **kw)

  builtins.print = log_print

  # tracer ------------------------------------------------
  def _trace(frame, event, arg):
    co = frame.f_code
    src = co.co_filename
    # skip non‑user frames and internal comprehensions
    if not src.endswith(USER_FILE):
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
          parent) if parent and parent.f_code.co_filename.endswith(USER_FILE) else 0
      if last_logged.get('CS_DEPTH') != depth_after:
        changes_local.append(('CS_DEPTH', depth_after))
        last_logged['CS_DEPTH'] = depth_after
      # restore caller locals (snapshot)
      if parent and parent.f_code.co_filename.endswith(USER_FILE):
        for var, val in parent.f_locals.items():
          if var.startswith('__') and var.endswith('__'):
            continue
          if var.endswith('_exc') or isinstance(
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
        if var.endswith('_exc') or isinstance(val, types.FunctionType):
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
        if gvar.endswith('_exc') or isinstance(
                gval, types.FunctionType):
          continue
        if gvar not in _prev_globals or _prev_globals[gvar] != gval:
          if last_logged.get(gvar) != gval:
            changes_local.append((gvar, copy.deepcopy(gval)))
            last_logged[gvar] = copy.deepcopy(gval)
          _prev_globals[gvar] = copy.deepcopy(gval)
      return _trace

    return _trace

  # run user code with tracer --------------------------------
  sys.settrace(_trace)
  namespace = {}
  with open(USER_FILE) as f:
    exec(compile(f.read(), USER_FILE, 'exec'), namespace)
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
# Interactive replay
# -------------------------------------------------------


all_changes = collect_changes()
columns = build_columns(all_changes)
row = {c: '' for c in columns}
rows = []


def display(rows):
  widths = {c: max(len(str(r.get(c, ''))) for r in rows +
                   [row for row in rows[-1:]] + [{c: c}]) + 2 for c in columns}
  sep = '+' + '+'.join('-' * widths[c] for c in columns) + '+'
  header = '|' + ''.join(f' {c}'.ljust(widths[c]) + '|' for c in columns)
  print(sep)
  print(header)
  print(sep)
  for r in rows:
    print(
        '|' +
        ''.join(
            f' {str(r.get(c, ""))}'.ljust(
                widths[c]) +
            '|' for c in columns))
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
