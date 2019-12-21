
import os
import sys

imageset = sys.argv[1]

for i in range(1,8):
    base = 'pro-set-' + imageset + '-part-'
    os.system('cp ' + base + '0.svg ' + base + str(i) + '.svg')
    os.system('cp ' + base + '0-failed.svg ' + base + str(i) + '-failed.svg')
