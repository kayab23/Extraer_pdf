import os
import sys
import subprocess
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ignore_dirs = ['.git', '__MACOSX']
# gather files
files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip .git and hidden system folders
    if any(ig in dirpath for ig in ignore_dirs):
        continue
    for f in filenames:
        files.append(os.path.join(dirpath, f))

# find .err files explicitly
err_files = [p for p in files if p.lower().endswith('.err')]

# find duplicates by basename
byname = defaultdict(list)
for p in files:
    byname[os.path.basename(p)].append(p)

duplicate_candidates = []
for name, paths in byname.items():
    if len(paths) > 1:
        # decide which to keep: prefer paths not containing '(1)', not in '__MACOSX', not in 'ARCHIVOS_NO_PEDIMENTOS'
        keep = None
        for p in paths:
            if '(1)' in p:
                continue
            if '__MACOSX' in p:
                continue
            if 'ARCHIVOS_NO_PEDIMENTOS' in p and any('PEDIMENTOS_VALIDOS' in q for q in paths):
                continue
            # prefer pedimentos_validos if present
            if 'PEDIMENTOS_VALIDOS' in p:
                keep = p
                break
            if keep is None:
                keep = p
        # mark others for deletion
        for p in paths:
            if p != keep:
                duplicate_candidates.append(p)

# build final delete list: .err files plus duplicates
to_delete = set(err_files + duplicate_candidates)

if not to_delete:
    print('No candidates found to delete.')
    sys.exit(0)

print('Files to delete (count={}):'.format(len(to_delete)))
for p in sorted(to_delete):
    print(p)

# prompt user confirmation if run interactively (but we assume user asked to delete)
print('\nProceeding to delete listed files...')

def safe_remove(path):
    try:
        # if tracked by git, use git rm
        rel = os.path.relpath(path, ROOT)
        # check if file is tracked
        res = subprocess.run(['git', 'ls-files', '--error-unmatch', rel], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            subprocess.run(['git', 'rm', '-f', rel], cwd=ROOT)
            print('git rm', rel)
        else:
            os.remove(path)
            print('os.remove', path)
    except Exception as e:
        print('ERROR removing', path, e)

for p in sorted(to_delete):
    safe_remove(p)

# commit and push deletions
try:
    subprocess.run(['git', 'commit', '-m', 'Remove .err and duplicate files (cleanup)'], cwd=ROOT)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT)
    print('Committed and pushed deletions.')
except Exception as e:
    print('Commit/push failed or no changes to commit.', e)
