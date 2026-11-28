import numpy as np
import colorsys
import pygame
import time
import math
import gmpy2
from decimal import Decimal, getcontext
from PIL import Image

pygame.init()
image = pygame.display.set_mode((1200, 800))
data = pygame.Surface([1200, 800])
CLEAR = pygame.Surface([1200, 800])
CLEAR.fill((255, 255, 255))

# shrug, color filtering is slow and table lookup is fast
COLORS = np.array([[255, 0, 0]], dtype=np.uint8)
for i in range(1, 255):
    COLORS = np.append(COLORS, [[255, i, 0]], axis=0)
for i in range(255):
    COLORS = np.append(COLORS, [[255 - i, 255, 0]], axis=0)
for i in range(255):
    COLORS = np.append(COLORS, [[0, 255, i]], axis=0)
for i in range(255):
    COLORS = np.append(COLORS, [[0, 255 - i, 255]], axis=0)
for i in range(255):
    COLORS = np.append(COLORS, [[i, 0, 255]], axis=0)
for i in range(255):
    COLORS = np.append(COLORS, [[255, 0, 255 - i]], axis=0)
COLORS = np.append(COLORS, [[0, 0, 0]], axis=0)
# The lookup has 1531 elements

TIME_RENDERS = True
LOADING_TEXT = "Rendering..."
# pygame why you no render text
loading_font = pygame.font.Font(None, 24)
loading = loading_font.render(LOADING_TEXT, True, (0, 0, 0))
LOADING_BG = pygame.Rect(0, 0, 100, 20)

data_mask = np.zeros((2, 1200, 800))
for i in range(1200):
    data_mask[0, i, :] = (i - 600) / 400
for i in range(800):
    data_mask[1, :, i] = (i - 400) / 400

def populate_data(rcenter = 0, icenter = -0.5, scale = 1):
    data = np.zeros((2, 1200, 800))
    data[0].fill(rcenter)
    data[1].fill(icenter)
    np.add(data, data_mask * scale, out=data)
    return data[0], data[1]

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
    '''
    # Blending pixels
    array_tl = pixels[:-1, :-1]
    array_tr = pixels[:-1, 1:]
    array_bl = pixels[1:, :-1]
    array_br = pixels[1:, 1:]

    out_pixels = np.zeros(pixels.shape)
    out_pixels[0, :] = pixels[0, :]
    out_pixels[:, 0] = pixels[:, 0]

    out_pixels[1:, 1:] = (array_tl + array_tr + array_bl + array_br) / 4
    out_pixels = out_pixels.astype(np.uint8)

    '''
    if outfile is not None:
        Image.fromarray(pixels).save(outfile)
    return pixels

def mandelbrot(data, iters = 50):
    c = np.array(data)
    final_count = np.zeros(c.shape[1:])
    final_count.fill(iters)
    z = np.zeros(c.shape)

    for i in range(iters):
        z2 = z * z
        mag2 = z2[0, :, :] + z2[1, :, :]
        nesc = mag2 < 4
        esc = np.logical_not(nesc)

        np.multiply(z[0, :, :], z[1, :, :], out=z[1, :, :], where=nesc)
        np.multiply(2.0, z[1, :, :], out=z[1, :, :], where=nesc)
        np.subtract(z2[0, :, :], z2[1, :, :], out=z[0, :, :], where=nesc)

        np.add(z, c, out=z, where=nesc)
        np.fmin(final_count, i, out=final_count, where=esc)

        print(z[:, 400, 600], i)

        yield final_count

def mandel_highprec(data, zoom, iters = 50):
    ctx = gmpy2.get_context()
    ctx.precision = max(53, math.ceil(16 - math.log2(zoom)))
    c = np.array(data)
    ref_cr = gmpy2.mpfr(c[0, 400, 600])
    ref_ci = gmpy2.mpfr(c[1, 400, 600])

    zr = gmpy2.mpfr('0')
    zi = gmpy2.mpfr('0')
    ref_orbit = []
    INFINITY = gmpy2.mpfr('179769313486231590772930519078902473361797697894230657273430081157732675805500963132708477322407536021120113879871393357658789768814416622492847430639474124377767893424865485276302219601246094119453082952085005768838150682342462881473913110540827237163350510684586298239947245938479716304835356329624224137215')
    
    for i in range(iters):
        zr2 = zr * zr
        zi2 = zi * zi

        if (zr2 + zi2) > INFINITY:
            for _ in range(iters - i):
                ref_orbit.append((INFINITY, INFINITY))
            break

        zi = 2 * zr * zi + ref_ci
        zr = zr2 - zi2 + ref_cr

        ref_orbit.append((zr, zi))

    print("computed reference orbit")

    epsilons_r = np.zeros((800, 1200), dtype=gmpy2.mpfr)
    epsilons_i = np.zeros((800, 1200), dtype=gmpy2.mpfr)
    deltas_r = np.array(data_mask[0, :, :], dtype=gmpy2.mpfr)
    deltas_i = np.array(data_mask[1, :, :], dtype=gmpy2.mpfr)

    epsilons_r[:] = gmpy2.mpfr(0)
    epsilons_i[:] = gmpy2.mpfr(0)

    _v = np.vectorize(gmpy2.mpfr)
    deltas_r[:] = _v(deltas_r * zoom)
    deltas_i[:] = _v(deltas_i * zoom)

    escaped = np.zeros((800, 1200))
    for i in range(iters):
        #for x in range(800):
        #    for y in range(1200):
        epsilons_r, epsilons_i = (
            2.0 * (ref_orbit[i][0] * epsilons_r - ref_orbit[i][1] * epsilons_i) + epsilons_r * epsilons_r - epsilons_i * epsilons_i + deltas_r, 
            2.0 * (epsilons_r * ref_orbit[i][1] + epsilons_i * ref_orbit[i][0] + epsilons_r * epsilons_i) + deltas_i
        )
        posr = epsilons_i + ref_orbit[i][0]
        posi = epsilons_r + ref_orbit[i][1]

        posr2 = posr * posr
        posi2 = posi * posi

        escaped[posr2 + posi2 > 4] = i

        print(posr[300, 500], posi[300, 500], i)

        print("iteration", i)

    return escaped

def update(a, b, c, d):
    global mandel, updated, glob_iter, TIME_RENDERS, data
    t = time.perf_counter()
    mandel = mandelbrot(populate_data(a, b, c), d)
    pixels = None
    since_last_update = time.time()
    for _ in range(d):
        pixels = next(mandel)
        if (time.time() - since_last_update > 0.05):
            pygame.surfarray.blit_array(data, COLORS[np.floor(pixels / d * 1530).astype(np.uint16)])
            image.blit(data)
            pygame.draw.rect(image, (255, 255, 255), LOADING_BG)
            image.blit(loading, loading.get_rect(center=(50, 10)))
            pygame.display.update()
            since_last_update = time.time()
            
    print("rendering took", round(time.perf_counter() - t, 3), "seconds")
    image.blit(data)
    pygame.display.update()
    updated = True

print("start draw")
# the expected things are reversed, imag moves x axis and real moves y axis
updated = True
window_running = True
is_selecting = False
is_dragging = False
selected_position = []
rect_other_corner = []

'''
update(0, -0.5, 1, 10)
hp_results = mandel_highprec(populate_data(0, -0.5, 1), 1, 10)
pygame.surfarray.blit_array(data, np.swapaxes(COLORS[np.floor(hp_results / 10 * 1530).astype(np.uint16)], 0, 1))
image.blit(data)
pygame.display.update()
time.sleep(10)
'''

#settings = (Decimal(0), Decimal(-0.5), 1)
settings = (-0.5, 0, 1)
glob_iter = 50
#settings = (-0.08100179833989508, -0.7585103961889802, 2.854753375053406e-13)
#glob_iter = 25600
update(*settings, glob_iter)
while window_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            window_running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not updated:
            if event.button == 1:
                is_selecting = True
            elif event.button == 3:
                print("drag")
                is_dragging = True
            selected_position = event.pos
            rect_other_corner = selected_position

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS:
                mul = 1.25
                if event.mod & pygame.KMOD_ALT:
                    mul = 2.0
                glob_iter = math.floor(glob_iter * mul)
                print("adding iterations, now", glob_iter)
                update(*settings, glob_iter)

            if event.key == pygame.K_MINUS:
                mul = 0.8
                if event.mod & pygame.KMOD_ALT:
                    mul = 0.5
                glob_iter = math.ceil(glob_iter * mul)
                print("removing iterations, now", glob_iter)
                update(*settings, glob_iter)

            if event.key == pygame.K_ESCAPE:
                is_selecting = False
                is_dragging = False
                image.blit(data)
            
            if event.key == pygame.K_r and event.mod & pygame.KMOD_SHIFT:
                print("reset parameters")
                settings = (-0.5, 0, 1)
                glob_iter = 50
                update(*settings, glob_iter)

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

        if is_dragging and event.type == pygame.MOUSEMOTION:
            rect_other_corner = event.pos

        if is_selecting and event.type == pygame.MOUSEBUTTONUP:
            top_left = (min(event.pos[0], selected_position[0]), min(event.pos[1], selected_position[1]))
            bottom_right = (max(event.pos[0], selected_position[0]), max(event.pos[1], selected_position[1]))

            if (abs(top_left[0] - bottom_right[0]) < 5): pass
            elif (not is_selecting): pass
            else:
                center = ((top_left[0] + bottom_right[0]) / 2, (top_left[1] + bottom_right[1]) / 2)
                center_coords = ((center[0] - 600) * settings[2] / 400, (center[1] - 400) * settings[2] / 400)

                settings = (settings[0] + center_coords[0], settings[1] + center_coords[1], settings[2] * (bottom_right[1] - top_left[1]) / 800)
                #print(top_left, bottom_right, center_coords, settings)
                #print("updating")
                is_selecting = False
                update(*settings, glob_iter)
                #print("finished")
                selected_position = (0, 0)

        if is_dragging and event.type == pygame.MOUSEBUTTONUP:
            offset = (rect_other_corner[0] - selected_position[0], rect_other_corner[1] - selected_position[1])
            settings = (settings[0] - (offset[0] / 400) * settings[2], settings[1] - (offset[1] / 400) * settings[2], settings[2])
            is_dragging = False
            update(*settings, glob_iter)
            selected_position = (0, 0)

    if not window_running: break

    if updated:
        print("last updated at", *settings, "with max iter", glob_iter)
        #pygame.surfarray.blit_array(data, np.swapaxes(mandel, 0, 1))
        updated = False
    
    if is_selecting:
        select_box = pygame.Rect(
            min(selected_position[0], rect_other_corner[0]), 
            min(selected_position[1], rect_other_corner[1]), 
            max(selected_position[0], rect_other_corner[0]) - min(selected_position[0], rect_other_corner[0]),
            max(selected_position[1], rect_other_corner[1]) - min(selected_position[1], rect_other_corner[1]),
        )

        image.blit(data)
        pygame.draw.rect(image, (120, 120, 120, 255), select_box, 1)

    if is_dragging:
        image.blit(CLEAR)
        image.blit(data, (rect_other_corner[0] - selected_position[0], rect_other_corner[1] - selected_position[1]))

    pygame.display.update()
    time.sleep(0.05)