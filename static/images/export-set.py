
import os

for j in range(8):
    for i in range(8):
        base = 'pro-set-' + str(j) + '-part-' + str(i)
        os.system('inkscape ' + base + '.svg --export-png=' + base + '.png')
        os.system('inkscape ' + base + '-failed.svg --export-png=' + base + '-failed.png')
        os.system('inkscape ' + base + '-icon.svg --export-png=' + base + '-icon.png')    
