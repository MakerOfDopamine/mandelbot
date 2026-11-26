import numpy as np
import colorsys
import pygame
import time
import math
from PIL import Image

pygame.init()
image = pygame.display.set_mode((1200, 800))
data = pygame.Surface([1200, 800])

TIME_RENDERS = True
LOADING_TEXT = "Rendering..."
# pygame why you no render text
loading_font = pygame.font.Font(None, 24)
loading = loading_font.render(LOADING_TEXT, True, (0, 0, 0))
LOADING_BG = pygame.Rect(0, 0, 100, 20)

# 900 x 600 window?
# Principle value of a pixel: top left

def populate_data(center = -0.5j, scale = 1):
    data_r = []
    data_i = []
    for i in range(800):
        row_r = []
        row_i = []
        for j in range(1200):
            row_r.append(((j - 600) * scale / 400) + center.imag)
            row_i.append(((i - 400) * scale / 400) + center.real)
        data_r.append(row_r[::])
        data_i.append(row_i[::])
    return np.array(data_r), np.array(data_i)

def col_abs_val(c):
    return np.array(colorsys.hls_to_rgb(abs(c) % 1, 0.5, 1)) * 255

def col_iters(c, mxi = 50):
    #if c > mxi: raise ValueError("c > mxi")
    return np.array(colorsys.hls_to_rgb(0.9 * ((c / mxi) % 1), (0 if c == mxi else 0.5), 1)) * 255

def draw(data, it, outfile = None):
    '''
    def _v(m1, m2, hue):
        hue = hue % 1.0
        if hue < ONE_SIXTH:
            return m1 + (m2-m1)*hue*6.0
        if hue < 0.5:
            return m2
        if hue < TWO_THIRD:
            return m1 + (m2-m1)*(TWO_THIRD-hue)*6.0
        return m1
    def hls_to_rgb(h, l, s):
        if s == 0.0:
            return l, l, l
        if l <= 0.5:
            m2 = l * (1.0+s)
        else:
            m2 = l+s-(l*s)
        m1 = 2.0*l - m2
        return (_v(m1, m2, h+ONE_THIRD), _v(m1, m2, h), _v(m1, m2, h-ONE_THIRD))
    '''
    ONE_THIRD = 1 / 3
    ONE_SIXTH = 1 / 6
    TWO_THIRD = 2 / 3

    pixels = np.zeros(data.shape + (3,), dtype=np.float64)

    black = (data >= it)
    ref_hue = (data / it) * 0.9
    scaled_hue = ref_hue * 255

    # m2 = 0.5 * (1 + 1.0) = 1
    # m1 = 1
    # Red breakpoints: x > 5/6, x < 1/6, x < 1/3
    # Green breakpoints: x < 1/6, x < 1/2, x < 2/3
    # Blue breakpoints: x < 1/2 and x > 1/3, x < 5/6 and x > 1/3, x < 1/3
    LT_ONE_SIXTH = (ref_hue <= ONE_SIXTH)
    LT_ONE_THIRD = (ref_hue <= ONE_THIRD)
    LT_ONE_HALF = (ref_hue <= 0.5)
    LT_TWO_THIRD = (ref_hue <= TWO_THIRD)
    LT_FIVE_SIXTH = (ref_hue <= (1 - ONE_SIXTH))

    GT_ONE_SIXTH = np.logical_not(LT_ONE_SIXTH)
    GT_ONE_THIRD = np.logical_not(LT_ONE_THIRD)
    GT_ONE_HALF = np.logical_not(LT_ONE_HALF)
    GT_TWO_THIRD = np.logical_not(LT_TWO_THIRD)
    GT_FIVE_SIXTH = np.logical_not(LT_FIVE_SIXTH)

    RED = pixels[:, :, 0]
    GREEN = pixels[:, :, 1]
    BLUE = pixels[:, :, 2]

    scaled_hue_red = ((scaled_hue - 170 + 255) % 255)
    scaled_hue_blue = ((scaled_hue + 170) % 255)

    pass
    # Set red channel
    np.add(RED, scaled_hue_red * 6, out=RED, where=np.logical_and(GT_TWO_THIRD, LT_FIVE_SIXTH))
    np.add(RED, 255, out=RED, where=np.logical_or(GT_FIVE_SIXTH, LT_ONE_SIXTH))
    np.add(RED, 255 - (scaled_hue_red - 128) * 6, out=RED, where=np.logical_and(GT_ONE_SIXTH, LT_ONE_THIRD))
    
    # Set green channel
    np.add(GREEN, scaled_hue * 6, out=GREEN, where=LT_ONE_SIXTH)
    np.add(GREEN, 255, out=GREEN, where=np.logical_and(GT_ONE_SIXTH, LT_ONE_HALF))
    np.add(GREEN, 255 - (scaled_hue - 128) * 6, out=GREEN, where=np.logical_and(GT_ONE_HALF, LT_TWO_THIRD))

    # Set blue channel
    np.add(BLUE, scaled_hue_blue * 6, out=BLUE, where=np.logical_and(LT_ONE_HALF, GT_ONE_THIRD))
    np.add(BLUE, 255, out=BLUE, where=np.logical_and(LT_FIVE_SIXTH, GT_ONE_HALF))
    np.add(BLUE, 255 - (scaled_hue_blue - 128) * 6, out=BLUE, where=GT_FIVE_SIXTH)

    # Redraw black pixels
    np.minimum(RED, 0, out=RED, where=black)
    np.minimum(GREEN, 0, out=GREEN, where=black)
    np.minimum(BLUE, 0, out=BLUE, where=black)

    pixels = pixels.astype(np.uint8)

    if outfile is not None:
        Image.fromarray(pixels).save(outfile)

    return pixels

def mandelbrot(data, iters = 50):
    t = time.perf_counter()

    c = np.array(data)
    final_count = np.zeros(rc.shape)
    final_count.fill(iters)
    rz, iz = np.zeros(rc.shape), np.zeros(ic.shape)

    for i in range(iters):
        rz2 = rz * rz
        iz2 = iz * iz

        nesc = (rz2 + iz2) < 4
        np.multiply(rz, iz, out=iz, where=nesc)
        np.multiply(2.0, iz, out=iz, where=nesc)
        np.subtract(rz2, iz2, out=rz, where=nesc)

        np.add(rz, rc, out=rz, where=nesc)
        np.add(iz, ic, out=iz, where=nesc)

        np.fmin(final_count, i, out=final_count, where=np.logical_not(esc))

    return final_count
    
    '''
    escape = np.zeros(data.shape, dtype=np.complex128)
    adder = np.array(data)
    results = np.zeros(data.shape)
    results.fill(iters)
    
    escaped_already = (abs(escape) > 2)
    print("preimaging took", time.perf_counter() - t); t = time.perf_counter()
    for k in range(iters):
        t = time.perf_counter()
        #escape = escape * escape + adder
        np.square(escape, out=escape, where=np.logical_not(escaped_already))
        print("squaring took", time.perf_counter() - t); t = time.perf_counter()
        np.add(escape, adder, out=escape, where=np.logical_not(escaped_already))
        print("adding took", time.perf_counter() - t); t = time.perf_counter()
        
        escaped_already = (abs(escape) > 2)
        print("compute escape took", time.perf_counter() - t); t = time.perf_counter()
        np.minimum(results, k, out=results, where=escaped_already)
        print("update took", time.perf_counter() - t); t = time.perf_counter()
    
    return results
    '''

def update(a, b, c, d):
    global mandel, updated, glob_iter, TIME_RENDERS
    t = time.perf_counter()
    mandel = draw(mandelbrot(populate_data(a+(b*1j), c), d), glob_iter)
    print("rendering took", round(time.perf_counter() - t, 3), "seconds")
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