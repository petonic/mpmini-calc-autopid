#!/usr/bin/env python3
#
#
import sys
import collections
import re

# 'sums' holds the dict of dicts. The major index is either
# 'c' or 'o' for classic or overshoot.  The minor index is
# one of 'p', 'i', 'd', 'c'.  'c' == count
sums = collections.defaultdict(float)

mode='-'

default_cycles=10

num_pids = 0

def usage():
  print('Usage: {} [infile]'.format(sys.argv[0]))
  print('\n\n\tTo perform the PID autotune in the terminal, type:')
  for x, y, z in (('EXTRUDER', 'M303', '240'), ('HEATED BED', 'M303 E-1', '110')):
    print('{} S{} C{}\t\t; Autotune PID for {}'.format(
        y, z, default_cycles, x))
  sys.exit(1)



if len(sys.argv)>1:
  arg = sys.argv[1]
  if arg == '--help':
    usage()
  if arg == '-' or arg == '--':
    arg = '/dev/stdin'
else:
  arg = '/dev/stdin'

val_re = r'''Recv:  K([pid]): ([0-9.]+)$'''
inTune = False
with open(arg) as infile:
  for line in infile:
    # print('--- ', line)
    if line.startswith('Recv: PID Autotune start'):
      # reinitialize the 'sums' dict
      sums = collections.defaultdict(float)
      inTune = True
      num_pids += 1
      continue

    # Indicates mode
    if line.startswith('Recv:  Classic PID'):
      # print('\tswitching to mode c')
      mode = 'c'
      continue
    if line.startswith('Recv:  Some overshoot'):
      # print('\tswitching to mode o')
      mode = 'o'
      continue

    # "Recv:  Kp: 33.49"
    match = re.search(val_re, line)
    if match:
      # print('\tvalmatch: mode={}, type={}, val={}'.format(
      #     mode, match.group(1), match.group(2)))

      sums[mode,match.group(1)] += float(match.group(2))
      if match.group(1) == 'd':
        sums[mode,'c'] += 1
        # print('\tEnd of PID sequence')
      continue

    if line.startswith('Recv: PID autotune finished.'):
      inTune = False
      break

if inTune:
  print('Error parsing input, still inTune state')
  sys.exit(1)

if num_pids < 1:
  print('Error, no PID Autotune cycles read from serial log')
  usage()

value = []

print('\tDone with Auto Calcing the Tuned PID\n')

for x, y in (('EXTRUDER', 'M301'), ('HEATED BED', 'M304')):
  print('\n\tFor the {}, use one of the following lines:'.format(x))
  for i in ['c', 'o']:
    print('{} '.format(y), end='')
    cnt = sums[i, 'c']
    for j in ['p', 'i', 'd']:
      print('{}{:.2f} '.format(j.upper(), float(sums[i,j]) / cnt), end='')
    print(';({} mode ({:.0f} values))'.format(
        'Classic' if i == 'c' else 'Overshoot',
        cnt ))
  print('\n')

print('\n\tFollowed by:\nM500   ;(WRITE TO FW and POWER CYCLE)')
