import numpy as np
import colorsys
import pygame
import time
import math
from PIL import Image

pygame.init()
image = pygame.display.set_mode((1200, 800))
data = pygame.Surface([1200, 800])

LOADING_TEXT = "Rendering..."
# pygame why you no render text
loading_font = pygame.font.Font(None, 24)
loading = loading_font.render(LOADING_TEXT, True, (0, 0, 0))
LOADING_BG = pygame.Rect(0, 0, 100, 20)

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
    return np.array(colorsys.hls_to_rgb(0.9 * ((c / mxi) % 1), (0 if c == mxi else 0.5), 1)) * 255

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
    escape = np.zeros(data.shape, dtype=np.complex128)
    adder = np.array(data)
    results = np.zeros(data.shape)
    results.fill(iters)
    
    escaped_already = (abs(escape) > 2)
    mag = np.zeros(data.shape, dtype=np.float64)
    for k in range(iters):
        #escape = escape * escape + adder
        np.square(escape, out=escape, where=np.logical_not(escaped_already))
        np.add(escape, adder, out=escape, where=np.logical_not(escaped_already))
        
        escaped_already = (abs(escape) > 2)
        np.minimum(results, k, out=results, where=escaped_already)
    
    return results

def update(a, b, c, d):
    global mandel, updated
    print("updating with", a, b, c, d)
    mandel = draw(mandelbrot(populate_data(a+(b*1j), c), d), col_iters)
    updated = True

def show_update_symbol(x):
    pygame.draw.rect(x, (255, 255, 255), LOADING_BG)
    x.blit(loading, loading.get_rect(center=(50, 10)))
    pygame.display.update()

print("start draw")
# the expected things are reversed, imag moves x axis and real moves y axis
updated = True
window_running = True
is_selecting = False
selected_position = []
rect_other_corner = []

settings = (0, -0.5, 1)
glob_iter = 50
update(*settings, glob_iter)
while window_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            window_running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            is_selecting = True
            selected_position = event.pos
            rect_other_corner = selected_position

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS:
                mul = 1.25
                if event.mod & pygame.KMOD_ALT:
                    mul = 2.0
                glob_iter = math.floor(glob_iter * mul)
                print("adding iterations, now", glob_iter)
                show_update_symbol(image)
                update(*settings, glob_iter)

            if event.key == pygame.K_MINUS:
                mul = 0.8
                if event.mod & pygame.KMOD_ALT:
                    mul = 0.5
                glob_iter = math.ceil(glob_iter * mul)
                print("removing iterations, now", glob_iter)
                show_update_symbol(image)
                update(*settings, glob_iter)

            if event.key == pygame.K_ESCAPE:
                is_selecting = False

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
            top_left = (min(event.pos[0], selected_position[0]), min(event.pos[1], selected_position[1]))
            bottom_right = (max(event.pos[0], selected_position[0]), max(event.pos[1], selected_position[1]))

            if (abs(top_left[0] - bottom_right[0]) < 5): pass
            elif (not is_selecting): pass
            else:
                center = ((top_left[0] + bottom_right[0]) / 2, (top_left[1] + bottom_right[1]) / 2)
                center_coords = ((center[1] - 400) * settings[2] / 400, (center[0] - 600) * settings[2] / 400)

                settings = (settings[0] + center_coords[0], settings[1] + center_coords[1], settings[2] * (bottom_right[1] - top_left[1]) / 800)
                #print(top_left, bottom_right, center_coords, settings)
                #print("updating")
                show_update_symbol(image)
                is_selecting = False
                update(*settings, glob_iter)
                #print("finished")
                selected_position = (0, 0)

    if not window_running: break

    if updated:
        print("last updated at", *settings, "with max iter", glob_iter)
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