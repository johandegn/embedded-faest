#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

def f(l, l_hat, t, t2):
    #k = l * (l_hat - l_hat/t2) - (l**2 + 2*l*t + l_hat*t)*(l_hat / t2)*t
    #k = 2**l *l_hat - 2**l * l_hat / t2 - l**2 * l_hat / t2 - 2 *l * l_hat * t / t2   - l_hat**2 * t / t2
    return k

l = 128
l_hat = 1280

#Create np array z with size l * l_hat
z = np.zeros((l_hat, l))

for t in range(1):
    for t2 in range(1, 8):
        z[t2][t] = f(l, l_hat, 32, t2)


#Plot the data
# add range of values of colors
plt.imshow(z, cmap='hot', interpolation='none')
plt.show()

print(f(128, 1280, 32, 1))
print(f(128, 1280, 32, 2))
        