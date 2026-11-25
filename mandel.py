import numpy as np
import colorsys
import pygame
import time
from PIL import Image

pygame.init()
image = pygame.display.set_mode((1200, 800))
data = pygame.Surface([1200, 800])

# 900 x 600 window?
# Principle value of a pixel: top left

def populate_data(center = -0.5j, scale = 1):
    data = []
    for i in range(800):
        row = []
        for j in range(1200):
            row.append(complex(((j - 600) * scale / 400) + center.imag, ((i - 400) * scale / 400) + center.real))
        data.append(row[::])
    return np.array(data)

def col_abs_val(c):
    return np.array(colorsys.hls_to_rgb(abs(c) % 1, 0.5, 1)) * 255

def col_iters(c, mxi = 50):
    #if c > mxi: raise ValueError("c > mxi")
    return np.array(colorsys.hls_to_rgb((c / mxi) % 1, (0 if c == mxi else 0.5), 1)) * 255

def draw(data, metric, outfile = None):
    pixels = np.zeros(data.shape + (3,), dtype=np.uint8)
    maximum_iters = data.max()
    for a, i in enumerate(data):
        for b, j in enumerate(i):
            pixels[a][b] = metric(j, maximum_iters)

    if outfile is not None:
        Image.fromarray(pixels).save(outfile)

    return pixels

def mandelbrot(data, iters = 50):
    escape = np.zeros(data.shape)
    for i in range(len(data)):
        for j in range(len(data[0])):
            z = 0+0j
            k = 0
            for _ in range(iters):
                z = z * z + data[i][j]
                k += 1
                if abs(z) > 2:
                    break
            escape[i][j] = k
                
    return escape

print("start draw")
# the expected things are reversed, imag moves x axis and real moves y axis
mandel = draw(mandelbrot(populate_data(0-0.5j, 1), 100), col_iters)
updated = True
window_running = True
is_selecting = False
selected_position = []
rect_other_corner = []
while window_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            window_running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            is_selecting = True
            selected_position = event.pos
            rect_other_corner = selected_position
            print(selected_position)

        if is_selecting and event.type == pygame.MOUSEMOTION:
            LR = event.pos[0] < selected_position[0]
            UD = event.pos[1] < selected_position[1]
            # fancy math shit when i just brute force it:
            if LR: # left
                if UD: # up
                    rect_scaling = min((selected_position[0] - event.pos[0]) / 1.5, (selected_position[1] - event.pos[1]))
                    rect_other_corner = (selected_position[0] - 1.5 * rect_scaling, selected_position[1] - rect_scaling)
                else: # down
                    rect_scaling = min((selected_position[0] - event.pos[0]) / 1.5, (event.pos[1] - selected_position[1]))
                    rect_other_corner = (selected_position[0] - 1.5 * rect_scaling, selected_position[1] + rect_scaling)
            else: # right
                if UD: # up
                    rect_scaling = min((event.pos[0] - selected_position[0]) / 1.5, (selected_position[1] - event.pos[1]))
                    rect_other_corner = (selected_position[0] + 1.5 * rect_scaling, selected_position[1] - rect_scaling)
                else: # down
                    rect_scaling = min((event.pos[0] - selected_position[0]) / 1.5, (event.pos[1] - selected_position[1]))
                    rect_other_corner = (selected_position[0] + 1.5 * rect_scaling, selected_position[1] + rect_scaling)

        if is_selecting and event.type == pygame.MOUSEBUTTONUP:
            is_selecting = False
            # zoom in ?

            print("mouse up")
            selected_position = (0, 0)

    if not window_running: break

    if updated:
        pygame.surfarray.blit_array(data, np.swapaxes(mandel, 0, 1))
        updated = False

    image.blit(data)
    if is_selecting:
        select_box = pygame.Rect(
            min(selected_position[0], rect_other_corner[0]), 
            min(selected_position[1], rect_other_corner[1]), 
            max(selected_position[0], rect_other_corner[0]) - min(selected_position[0], rect_other_corner[0]),
            max(selected_position[1], rect_other_corner[1]) - min(selected_position[1], rect_other_corner[1]),
        )

        pygame.draw.rect(image, (120, 120, 120, 255), select_box, 1)

    pygame.display.update()
    time.sleep(0.05)